import os
import secrets
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Optional

import bcrypt
import jwt
from dotenv import load_dotenv
from fastapi import Depends, FastAPI, HTTPException, Request, Response
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, ConfigDict, EmailStr, Field
from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, or_, select
from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / ".env")

DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./schemesaathi.db")
connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-local-secret")
ALGORITHM = "HS256"


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
    password_hash: Mapped[str] = mapped_column(String(255))
    role: Mapped[str] = mapped_column(String(20), default="citizen")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")


class Profile(Base):
    __tablename__ = "profiles"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    state: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    education: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    occupation: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
    user: Mapped[User] = relationship(back_populates="profile")


class Scheme(Base):
    __tablename__ = "schemes"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(180), index=True)
    name_hi: Mapped[str] = mapped_column(String(180))
    ministry: Mapped[str] = mapped_column(String(180))
    category: Mapped[str] = mapped_column(String(80), index=True)
    level: Mapped[str] = mapped_column(String(40))
    state: Mapped[str] = mapped_column(String(80), default="All India")
    summary: Mapped[str] = mapped_column(Text)
    benefits: Mapped[str] = mapped_column(Text)
    documents: Mapped[str] = mapped_column(Text)
    process: Mapped[str] = mapped_column(Text)
    source_url: Mapped[str] = mapped_column(String(500))
    verified_date: Mapped[str] = mapped_column(String(30))
    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    max_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    income_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    target_occupation: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
    verified: Mapped[bool] = mapped_column(Boolean, default=True)


class SavedScheme(Base):
    __tablename__ = "saved_schemes"
    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id"))


Base.metadata.create_all(engine)

app = FastAPI(title="SchemeSaathi API", version="1.0.0")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://eligibility-finder-16.preview.emergentagent.com"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
FAILED_LOGINS = {}


def db_session():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()


def verify_password(password: str, hashed: str) -> bool:
    return bcrypt.checkpw(password.encode(), hashed.encode())


def token_for(user: User) -> str:
    return jwt.encode({"sub": str(user.id), "email": user.email, "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, JWT_SECRET, algorithm=ALGORITHM)


def user_payload(user: User):
    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}


def current_user(request: Request, db: Session = Depends(db_session)) -> User:
    token = request.cookies.get("access_token")
    auth = request.headers.get("Authorization", "")
    if not token and auth.startswith("Bearer "):
        token = auth[7:]
    if not token:
        raise HTTPException(401, "Please sign in to continue")
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
        user = db.get(User, int(payload["sub"]))
    except (jwt.InvalidTokenError, KeyError, ValueError):
        user = None
    if not user:
        raise HTTPException(401, "Your session has expired")
    return user


class AuthInput(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class RegisterInput(AuthInput):
    name: str = Field(min_length=2, max_length=120)


class ProfileInput(BaseModel):
    age: Optional[int] = Field(default=None, ge=1, le=120)
    state: Optional[str] = None
    income: Optional[float] = Field(default=None, ge=0)
    education: Optional[str] = None
    occupation: Optional[str] = None
    category: Optional[str] = None


class SchemeInput(BaseModel):
    name: str
    name_hi: str
    ministry: str
    category: str
    level: str
    state: str = "All India"
    summary: str
    benefits: str
    documents: str
    process: str
    source_url: str
    verified_date: str
    min_age: Optional[int] = None
    max_age: Optional[int] = None
    income_limit: Optional[float] = None
    target_occupation: Optional[str] = None


def scheme_dict(s: Scheme):
    return {"id": s.id, "name": s.name, "name_hi": s.name_hi, "ministry": s.ministry, "category": s.category, "level": s.level, "state": s.state, "summary": s.summary, "benefits": s.benefits.split("|"), "documents": s.documents.split("|"), "process": s.process.split("|"), "source_url": s.source_url, "verified_date": s.verified_date, "min_age": s.min_age, "max_age": s.max_age, "income_limit": s.income_limit, "target_occupation": s.target_occupation, "verified": s.verified}


@app.get("/api/")
def root():
    return {"message": "SchemeSaathi is ready"}


@app.post("/api/auth/register")
def register(data: RegisterInput, response: Response, db: Session = Depends(db_session)):
    email = data.email.lower()
    if db.scalar(select(User).where(User.email == email)):
        raise HTTPException(409, "An account with this email already exists")
    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
    db.add(user); db.commit(); db.refresh(user)
    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=28800)
    return user_payload(user)


@app.post("/api/auth/login")
def login(data: AuthInput, response: Response, db: Session = Depends(db_session)):
    email = data.email.lower()
    attempt = FAILED_LOGINS.get(email)
    if attempt and attempt["until"] > datetime.now(timezone.utc):
        raise HTTPException(429, "Too many attempts. Please try again in a few minutes")
    user = db.scalar(select(User).where(User.email == email))
    if not user or not verify_password(data.password, user.password_hash):
        current = FAILED_LOGINS.get(email, {"count": 0, "until": datetime.now(timezone.utc)})
        current["count"] += 1
        if current["count"] >= 5:
            current["until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
        FAILED_LOGINS[email] = current
        raise HTTPException(401, "Email or password is incorrect")
    FAILED_LOGINS.pop(email, None)
    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=28800)
    return user_payload(user)


@app.post("/api/auth/logout")
def logout(response: Response):
    response.delete_cookie("access_token")
    return {"message": "Signed out"}


@app.get("/api/auth/me")
def me(user: User = Depends(current_user)):
    return user_payload(user)


@app.get("/api/schemes")
def schemes(search: str = "", category: str = "All", state: str = "All", db: Session = Depends(db_session)):
    query = select(Scheme).where(Scheme.verified == True)
    if search:
        term = f"%{search}%"; query = query.where(or_(Scheme.name.ilike(term), Scheme.summary.ilike(term), Scheme.ministry.ilike(term)))
    if category != "All": query = query.where(Scheme.category == category)
    if state != "All": query = query.where(or_(Scheme.state == state, Scheme.state == "All India"))
    return [scheme_dict(s) for s in db.scalars(query.order_by(Scheme.id)).all()]


@app.get("/api/schemes/{scheme_id}")
def scheme_detail(scheme_id: int, db: Session = Depends(db_session)):
    scheme = db.get(Scheme, scheme_id)
    if not scheme: raise HTTPException(404, "Scheme not found")
    return scheme_dict(scheme)


@app.get("/api/profile")
def get_profile(user: User = Depends(current_user), db: Session = Depends(db_session)):
    p = db.scalar(select(Profile).where(Profile.user_id == user.id))
    return {"name": user.name, **({k: getattr(p, k) for k in ["age", "state", "income", "education", "occupation", "category"]} if p else {})}


@app.put("/api/profile")
def save_profile(data: ProfileInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    p = db.scalar(select(Profile).where(Profile.user_id == user.id))
    if not p: p = Profile(user_id=user.id); db.add(p)
    for key, value in data.model_dump().items(): setattr(p, key, value)
    db.commit()
    return {"message": "Profile saved", **data.model_dump()}


@app.post("/api/eligibility/check")
def check_eligibility(data: ProfileInput, db: Session = Depends(db_session)):
    results = []
    for s in db.scalars(select(Scheme).where(Scheme.verified == True)).all():
        missing = []
        matches = []
        failures = []
        if data.age is None: missing.append("age")
        elif s.min_age and data.age < s.min_age: failures.append(f"Age {s.min_age}+ required")
        elif s.max_age and data.age > s.max_age: failures.append(f"Age up to {s.max_age} required")
        else: matches.append("Age range matches")
        if not data.state: missing.append("state")
        elif s.state != "All India" and data.state != s.state: failures.append(f"Only available in {s.state}")
        else: matches.append("Location matches")
        if s.income_limit is not None:
            if data.income is None: missing.append("annual income")
            elif data.income > s.income_limit: failures.append("Income limit not met")
            else: matches.append("Income limit matches")
        if s.target_occupation:
            if not data.occupation: missing.append("occupation")
            elif s.target_occupation.lower() not in data.occupation.lower(): failures.append(f"This scheme is for {s.target_occupation} applicants")
            else: matches.append("Occupation matches")
        status = "Needs More Information" if missing else ("Not Eligible" if failures else "Eligible")
        results.append({"scheme": scheme_dict(s), "status": status, "matches": matches, "failures": failures, "missing": missing})
    return results


@app.get("/api/saved")
def saved(user: User = Depends(current_user), db: Session = Depends(db_session)):
    rows = db.scalars(select(SavedScheme).where(SavedScheme.user_id == user.id)).all()
    return [scheme_dict(db.get(Scheme, row.scheme_id)) for row in rows]


@app.post("/api/saved/{scheme_id}")
def save_scheme(scheme_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    if not db.get(Scheme, scheme_id): raise HTTPException(404, "Scheme not found")
    if not db.scalar(select(SavedScheme).where(SavedScheme.user_id == user.id, SavedScheme.scheme_id == scheme_id)):
        db.add(SavedScheme(user_id=user.id, scheme_id=scheme_id)); db.commit()
    return {"saved": True}


@app.delete("/api/saved/{scheme_id}")
def unsave_scheme(scheme_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
    row = db.scalar(select(SavedScheme).where(SavedScheme.user_id == user.id, SavedScheme.scheme_id == scheme_id))
    if row: db.delete(row); db.commit()
    return {"saved": False}


@app.post("/api/admin/schemes")
def admin_create(data: SchemeInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
    if user.role != "admin": raise HTTPException(403, "Admin access required")
    scheme = Scheme(**data.model_dump()); db.add(scheme); db.commit(); db.refresh(scheme)
    return scheme_dict(scheme)


def seed_data(db: Session):
    if db.scalar(select(Scheme.id)): return
    rows = [
        ("PM-KISAN", "पीएम-किसान", "Ministry of Agriculture & Farmers Welfare", "Farmers", "Central", "All India", "Income support for eligible landholding farmer families.", "₹6,000 annual support in three instalments", "Aadhaar|Land ownership records|Bank account details", "Verify details on the official portal|Complete e-KYC|Track instalments", "https://pmkisan.gov.in/", "2025-02-01", None, None, None, "Farmer"),
        ("Pradhan Mantri Fasal Bima Yojana", "प्रधानमंत्री फसल बीमा योजना", "Ministry of Agriculture & Farmers Welfare", "Farmers", "Central", "All India", "Crop insurance support against notified crop risks.", "Insurance coverage and financial support as per notified terms", "Aadhaar|Land records|Bank details|Sowing declaration", "Contact a bank or CSC|Submit crop and land details|Keep acknowledgement", "https://pmfby.gov.in/", "2025-01-15", None, None, None, "Farmer"),
        ("Post Matric Scholarship (MP)", "पोस्ट मैट्रिक छात्रवृत्ति (म.प्र.)", "Tribal Affairs / Social Justice, Madhya Pradesh", "Students", "State", "Madhya Pradesh", "Scholarship information for eligible post-matric students in Madhya Pradesh.", "Support towards approved educational expenses as per current notification", "Aadhaar|Caste certificate|Income certificate|Bonafide certificate|Bank details", "Register on the state scholarship portal|Upload documents|Submit to institution", "https://hescholarship.mp.gov.in/", "2025-01-10", None, None, 250000, "Student"),
        ("Mukhyamantri Seekho Kamao Yojana", "मुख्यमंत्री सीखो कमाओ योजना", "Government of Madhya Pradesh", "Youth & Jobs", "State", "Madhya Pradesh", "On-the-job training and stipend information for eligible youth.", "Training exposure and stipend subject to current programme rules", "Aadhaar|Education certificate|Bank account|Residence proof", "Create profile on the official portal|Choose a course|Apply to an establishment", "https://mmsky.mp.gov.in/", "2025-02-12", 18, 29, None, "Job seeker"),
        ("PM SVANidhi", "पीएम स्वनिधि", "Ministry of Housing & Urban Affairs", "Entrepreneurs", "Central", "All India", "Working capital support for street vendors through participating lenders.", "Working capital loan and incentives subject to lender terms", "Aadhaar|Vendor certificate or survey reference|Bank details", "Approach a lending institution or apply through the official portal|Submit verification", "https://pmsvanidhi.mohua.gov.in/", "2025-01-20", None, None, None, "Entrepreneur"),
        ("Stand-Up India", "स्टैंड-अप इंडिया", "Department of Financial Services", "Women", "Central", "All India", "Bank loans for greenfield enterprises promoted by women and SC/ST entrepreneurs.", "Composite loan support subject to bank appraisal and scheme terms", "Identity proof|Address proof|Business plan|Category certificate where applicable", "Use the official portal|Connect with a bank|Submit project proposal", "https://www.standupmitra.in/", "2025-02-05", 18, None, None, "Entrepreneur"),
        ("PMAY-Gramin", "प्रधानमंत्री आवास योजना-ग्रामीण", "Ministry of Rural Development", "Housing", "Central", "All India", "Housing assistance information for eligible rural households.", "Housing assistance as per programme guidelines and local verification", "Aadhaar|Residence proof|Household details|Bank account", "Check inclusion with the Gram Panchayat|Complete verification|Follow local process", "https://pmayg.nic.in/", "2025-01-30", None, None, None, None),
        ("National Career Service", "राष्ट्रीय करियर सेवा", "Ministry of Labour & Employment", "Youth & Jobs", "Central", "All India", "Career discovery, counselling and job matching services for citizens.", "Job search, counselling and career resources", "Aadhaar or mobile number|Education details|Resume details", "Create a profile|Search opportunities|Apply directly where available", "https://www.ncs.gov.in/", "2025-02-08", 18, None, None, "Job seeker"),
        ("Beti Bachao Beti Padhao", "बेटी बचाओ बेटी पढ़ाओ", "Ministry of Women & Child Development", "Women", "Central", "All India", "Awareness and support programme promoting the rights and education of the girl child.", "Local programme support and awareness services; verify offerings locally", "Identity proof|Residence proof|School details where relevant", "Contact the district women and child development office|Verify local support", "https://wcd.nic.in/bbbp-scheme", "2025-01-18", None, None, None, None),
    ]
    for row in rows: db.add(Scheme(name=row[0], name_hi=row[1], ministry=row[2], category=row[3], level=row[4], state=row[5], summary=row[6], benefits=row[7], documents=row[8], process=row[9], source_url=row[10], verified_date=row[11], min_age=row[12], max_age=row[13], income_limit=row[14], target_occupation=row[15]))
    db.commit()


@app.on_event("startup")
def startup():
    db = SessionLocal()
    try:
        admin_email = os.environ.get("ADMIN_EMAIL", "admin@schemesaathi.demo")
        admin_password = os.environ.get("ADMIN_PASSWORD", "SchemeSaathi123!")
        admin = db.scalar(select(User).where(User.email == admin_email))
        if not admin:
            db.add(User(name="SchemeSaathi Admin", email=admin_email, password_hash=hash_password(admin_password), role="admin")); db.commit()
        elif not verify_password(admin_password, admin.password_hash):
            admin.password_hash = hash_password(admin_password); db.commit()
        seed_data(db)
    finally: db.close()
