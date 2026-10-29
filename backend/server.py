I’ll retrieve the current backend file exactly as implemented and share it in one complete code block.
Action: view_file({"path":"/app/backend/server.py","view_range":[1,1000]})
Observation: [Showing lines 1-335 of 335 total] /app/backend/server.py:
1|import os
2|import secrets
3|from datetime import datetime, timedelta, timezone
4|from pathlib import Path
5|from typing import Optional
6|
7|import bcrypt
8|import jwt
9|from dotenv import load_dotenv
10|from fastapi import Depends, FastAPI, HTTPException, Request, Response
11|from fastapi.middleware.cors import CORSMiddleware
12|from pydantic import BaseModel, ConfigDict, EmailStr, Field
13|from sqlalchemy import Boolean, DateTime, Float, ForeignKey, Integer, String, Text, create_engine, or_, select
14|from sqlalchemy.orm import DeclarativeBase, Mapped, Session, mapped_column, relationship, sessionmaker
15|
16|ROOT_DIR = Path(__file__).parent
17|load_dotenv(ROOT_DIR / ".env")
18|
19|DATABASE_URL = os.environ.get("DATABASE_URL", "sqlite:///./schemesaathi.db")
20|connect_args = {"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {}
21|engine = create_engine(DATABASE_URL, connect_args=connect_args, pool_pre_ping=True)
22|SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
23|JWT_SECRET = os.environ.get("JWT_SECRET", "change-this-local-secret")
24|ALGORITHM = "HS256"
25|
26|
27|class Base(DeclarativeBase):
28|    pass
29|
30|
31|class User(Base):
32|    __tablename__ = "users"
33|    id: Mapped[int] = mapped_column(primary_key=True)
34|    name: Mapped[str] = mapped_column(String(120))
35|    email: Mapped[str] = mapped_column(String(255), unique=True, index=True)
36|    password_hash: Mapped[str] = mapped_column(String(255))
37|    role: Mapped[str] = mapped_column(String(20), default="citizen")
38|    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
39|    profile: Mapped[Optional["Profile"]] = relationship(back_populates="user", uselist=False, cascade="all, delete-orphan")
40|
41|
42|class Profile(Base):
43|    __tablename__ = "profiles"
44|    id: Mapped[int] = mapped_column(primary_key=True)
45|    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), unique=True)
46|    age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
47|    state: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
48|    income: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
49|    education: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
50|    occupation: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
51|    category: Mapped[Optional[str]] = mapped_column(String(80), nullable=True)
52|    user: Mapped[User] = relationship(back_populates="profile")
53|
54|
55|class Scheme(Base):
56|    __tablename__ = "schemes"
57|    id: Mapped[int] = mapped_column(primary_key=True)
58|    name: Mapped[str] = mapped_column(String(180), index=True)
59|    name_hi: Mapped[str] = mapped_column(String(180))
60|    ministry: Mapped[str] = mapped_column(String(180))
61|    category: Mapped[str] = mapped_column(String(80), index=True)
62|    level: Mapped[str] = mapped_column(String(40))
63|    state: Mapped[str] = mapped_column(String(80), default="All India")
64|    summary: Mapped[str] = mapped_column(Text)
65|    benefits: Mapped[str] = mapped_column(Text)
66|    documents: Mapped[str] = mapped_column(Text)
67|    process: Mapped[str] = mapped_column(Text)
68|    source_url: Mapped[str] = mapped_column(String(500))
69|    verified_date: Mapped[str] = mapped_column(String(30))
70|    min_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
71|    max_age: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
72|    income_limit: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
73|    target_occupation: Mapped[Optional[str]] = mapped_column(String(120), nullable=True)
74|    verified: Mapped[bool] = mapped_column(Boolean, default=True)
75|
76|
77|class SavedScheme(Base):
78|    __tablename__ = "saved_schemes"
79|    id: Mapped[int] = mapped_column(primary_key=True)
80|    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"))
81|    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id"))
82|
83|
84|Base.metadata.create_all(engine)
85|
86|app = FastAPI(title="SchemeSaathi API", version="1.0.0")
87|app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:3000", "https://eligibility-finder-16.preview.emergentagent.com"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])
88|FAILED_LOGINS = {}
89|
90|
91|def db_session():
92|    db = SessionLocal()
93|    try:
94|        yield db
95|    finally:
96|        db.close()
97|
98|
99|def hash_password(password: str) -> str:
100|    return bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()
101|
102|
103|def verify_password(password: str, hashed: str) -> bool:
104|    return bcrypt.checkpw(password.encode(), hashed.encode())
105|
106|
107|def token_for(user: User) -> str:
108|    return jwt.encode({"sub": str(user.id), "email": user.email, "role": user.role, "exp": datetime.now(timezone.utc) + timedelta(hours=8)}, JWT_SECRET, algorithm=ALGORITHM)
109|
110|
111|def user_payload(user: User):
112|    return {"id": user.id, "name": user.name, "email": user.email, "role": user.role}
113|
114|
115|def current_user(request: Request, db: Session = Depends(db_session)) -> User:
116|    token = request.cookies.get("access_token")
117|    auth = request.headers.get("Authorization", "")
118|    if not token and auth.startswith("Bearer "):
119|        token = auth[7:]
120|    if not token:
121|        raise HTTPException(401, "Please sign in to continue")
122|    try:
123|        payload = jwt.decode(token, JWT_SECRET, algorithms=[ALGORITHM])
124|        user = db.get(User, int(payload["sub"]))
125|    except (jwt.InvalidTokenError, KeyError, ValueError):
126|        user = None
127|    if not user:
128|        raise HTTPException(401, "Your session has expired")
129|    return user
130|
131|
132|class AuthInput(BaseModel):
133|    email: EmailStr
134|    password: str = Field(min_length=8)
135|
136|
137|class RegisterInput(AuthInput):
138|    name: str = Field(min_length=2, max_length=120)
139|
140|
141|class ProfileInput(BaseModel):
142|    age: Optional[int] = Field(default=None, ge=1, le=120)
143|    state: Optional[str] = None
144|    income: Optional[float] = Field(default=None, ge=0)
145|    education: Optional[str] = None
146|    occupation: Optional[str] = None
147|    category: Optional[str] = None
148|
149|
150|class SchemeInput(BaseModel):
151|    name: str
152|    name_hi: str
153|    ministry: str
154|    category: str
155|    level: str
156|    state: str = "All India"
157|    summary: str
158|    benefits: str
159|    documents: str
160|    process: str
161|    source_url: str
162|    verified_date: str
163|    min_age: Optional[int] = None
164|    max_age: Optional[int] = None
165|    income_limit: Optional[float] = None
166|    target_occupation: Optional[str] = None
167|
168|
169|def scheme_dict(s: Scheme):
170|    return {"id": s.id, "name": s.name, "name_hi": s.name_hi, "ministry": s.ministry, "category": s.category, "level": s.level, "state": s.state, "summary": s.summary, "benefits": s.benefits.split("|"), "documents": s.documents.split("|"), "process": s.process.split("|"), "source_url": s.source_url, "verified_date": s.verified_date, "min_age": s.min_age, "max_age": s.max_age, "income_limit": s.income_limit, "target_occupation": s.target_occupation, "verified": s.verified}
171|
172|
173|@app.get("/api/")
174|def root():
175|    return {"message": "SchemeSaathi is ready"}
176|
177|
178|@app.post("/api/auth/register")
179|def register(data: RegisterInput, response: Response, db: Session = Depends(db_session)):
180|    email = data.email.lower()
181|    if db.scalar(select(User).where(User.email == email)):
182|        raise HTTPException(409, "An account with this email already exists")
183|    user = User(name=data.name, email=email, password_hash=hash_password(data.password))
184|    db.add(user); db.commit(); db.refresh(user)
185|    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=28800)
186|    return user_payload(user)
187|
188|
189|@app.post("/api/auth/login")
190|def login(data: AuthInput, response: Response, db: Session = Depends(db_session)):
191|    email = data.email.lower()
192|    attempt = FAILED_LOGINS.get(email)
193|    if attempt and attempt["until"] > datetime.now(timezone.utc):
194|        raise HTTPException(429, "Too many attempts. Please try again in a few minutes")
195|    user = db.scalar(select(User).where(User.email == email))
196|    if not user or not verify_password(data.password, user.password_hash):
197|        current = FAILED_LOGINS.get(email, {"count": 0, "until": datetime.now(timezone.utc)})
198|        current["count"] += 1
199|        if current["count"] >= 5:
200|            current["until"] = datetime.now(timezone.utc) + timedelta(minutes=15)
201|        FAILED_LOGINS[email] = current
202|        raise HTTPException(401, "Email or password is incorrect")
203|    FAILED_LOGINS.pop(email, None)
204|    response.set_cookie("access_token", token_for(user), httponly=True, samesite="lax", max_age=28800)
205|    return user_payload(user)
206|
207|
208|@app.post("/api/auth/logout")
209|def logout(response: Response):
210|    response.delete_cookie("access_token")
211|    return {"message": "Signed out"}
212|
213|
214|@app.get("/api/auth/me")
215|def me(user: User = Depends(current_user)):
216|    return user_payload(user)
217|
218|
219|@app.get("/api/schemes")
220|def schemes(search: str = "", category: str = "All", state: str = "All", db: Session = Depends(db_session)):
221|    query = select(Scheme).where(Scheme.verified == True)
222|    if search:
223|        term = f"%{search}%"; query = query.where(or_(Scheme.name.ilike(term), Scheme.summary.ilike(term), Scheme.ministry.ilike(term)))
224|    if category != "All": query = query.where(Scheme.category == category)
225|    if state != "All": query = query.where(or_(Scheme.state == state, Scheme.state == "All India"))
226|    return [scheme_dict(s) for s in db.scalars(query.order_by(Scheme.id)).all()]
227|
228|
229|@app.get("/api/schemes/{scheme_id}")
230|def scheme_detail(scheme_id: int, db: Session = Depends(db_session)):
231|    scheme = db.get(Scheme, scheme_id)
232|    if not scheme: raise HTTPException(404, "Scheme not found")
233|    return scheme_dict(scheme)
234|
235|
236|@app.get("/api/profile")
237|def get_profile(user: User = Depends(current_user), db: Session = Depends(db_session)):
238|    p = db.scalar(select(Profile).where(Profile.user_id == user.id))
239|    return {"name": user.name, **({k: getattr(p, k) for k in ["age", "state", "income", "education", "occupation", "category"]} if p else {})}
240|
241|
242|@app.put("/api/profile")
243|def save_profile(data: ProfileInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
244|    p = db.scalar(select(Profile).where(Profile.user_id == user.id))
245|    if not p: p = Profile(user_id=user.id); db.add(p)
246|    for key, value in data.model_dump().items(): setattr(p, key, value)
247|    db.commit()
248|    return {"message": "Profile saved", **data.model_dump()}
249|
250|
251|@app.post("/api/eligibility/check")
252|def check_eligibility(data: ProfileInput, db: Session = Depends(db_session)):
253|    results = []
254|    for s in db.scalars(select(Scheme).where(Scheme.verified == True)).all():
255|        missing = []
256|        matches = []
257|        failures = []
258|        if data.age is None: missing.append("age")
259|        elif s.min_age and data.age < s.min_age: failures.append(f"Age {s.min_age}+ required")
260|        elif s.max_age and data.age > s.max_age: failures.append(f"Age up to {s.max_age} required")
261|        else: matches.append("Age range matches")
262|        if not data.state: missing.append("state")
263|        elif s.state != "All India" and data.state != s.state: failures.append(f"Only available in {s.state}")
264|        else: matches.append("Location matches")
265|        if s.income_limit is not None:
266|            if data.income is None: missing.append("annual income")
267|            elif data.income > s.income_limit: failures.append("Income limit not met")
268|            else: matches.append("Income limit matches")
269|        if s.target_occupation:
270|            if not data.occupation: missing.append("occupation")
271|            elif s.target_occupation.lower() not in data.occupation.lower(): failures.append(f"This scheme is for {s.target_occupation} applicants")
272|            else: matches.append("Occupation matches")
273|        status = "Needs More Information" if missing else ("Not Eligible" if failures else "Eligible")
274|        results.append({"scheme": scheme_dict(s), "status": status, "matches": matches, "failures": failures, "missing": missing})
275|    return results
276|
277|
278|@app.get("/api/saved")
279|def saved(user: User = Depends(current_user), db: Session = Depends(db_session)):
280|    rows = db.scalars(select(SavedScheme).where(SavedScheme.user_id == user.id)).all()
281|    return [scheme_dict(db.get(Scheme, row.scheme_id)) for row in rows]
282|
283|
284|@app.post("/api/saved/{scheme_id}")
285|def save_scheme(scheme_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
286|    if not db.get(Scheme, scheme_id): raise HTTPException(404, "Scheme not found")
287|    if not db.scalar(select(SavedScheme).where(SavedScheme.user_id == user.id, SavedScheme.scheme_id == scheme_id)):
288|        db.add(SavedScheme(user_id=user.id, scheme_id=scheme_id)); db.commit()
289|    return {"saved": True}
290|
291|
292|@app.delete("/api/saved/{scheme_id}")
293|def unsave_scheme(scheme_id: int, user: User = Depends(current_user), db: Session = Depends(db_session)):
294|    row = db.scalar(select(SavedScheme).where(SavedScheme.user_id == user.id, SavedScheme.scheme_id == scheme_id))
295|    if row: db.delete(row); db.commit()
296|    return {"saved": False}
297|
298|
299|@app.post("/api/admin/schemes")
300|def admin_create(data: SchemeInput, user: User = Depends(current_user), db: Session = Depends(db_session)):
301|    if user.role != "admin": raise HTTPException(403, "Admin access required")
302|    scheme = Scheme(**data.model_dump()); db.add(scheme); db.commit(); db.refresh(scheme)
303|    return scheme_dict(scheme)
304|
305|
306|def seed_data(db: Session):
307|    if db.scalar(select(Scheme.id)): return
308|    rows = [
309|        ("PM-KISAN", "पीएम-किसान", "Ministry of Agriculture & Farmers Welfare", "Farmers", "Central", "All India", "Income support for eligible landholding farmer families.", "₹6,000 annual support in three instalments", "Aadhaar|Land ownership records|Bank account details", "Verify details on the official portal|Complete e-KYC|Track instalments", "https://pmkisan.gov.in/", "2025-02-01", None, None, None, "Farmer"),
310|        ("Pradhan Mantri Fasal Bima Yojana", "प्रधानमंत्री फसल बीमा योजना", "Ministry of Agriculture & Farmers Welfare", "Farmers", "Central", "All India", "Crop insurance support against notified crop risks.", "Insurance coverage and financial support as per notified terms", "Aadhaar|Land records|Bank details|Sowing declaration", "Contact a bank or CSC|Submit crop and land details|Keep acknowledgement", "https://pmfby.gov.in/", "2025-01-15", None, None, None, "Farmer"),
311|        ("Post Matric Scholarship (MP)", "पोस्ट मैट्रिक छात्रवृत्ति (म.प्र.)", "Tribal Affairs / Social Justice, Madhya Pradesh", "Students", "State", "Madhya Pradesh", "Scholarship information for eligible post-matric students in Madhya Pradesh.", "Support towards approved educational expenses as per current notification", "Aadhaar|Caste certificate|Income certificate|Bonafide certificate|Bank details", "Register on the state scholarship portal|Upload documents|Submit to institution", "https://hescholarship.mp.gov.in/", "2025-01-10", None, 250000, None, "Student"),
312|        ("Mukhyamantri Seekho Kamao Yojana", "मुख्यमंत्री सीखो कमाओ योजना", "Government of Madhya Pradesh", "Youth & Jobs", "State", "Madhya Pradesh", "On-the-job training and stipend information for eligible youth.", "Training exposure and stipend subject to current programme rules", "Aadhaar|Education certificate|Bank account|Residence proof", "Create profile on the official portal|Choose a course|Apply to an establishment", "https://mmsky.mp.gov.in/", "2025-02-12", 18, 29, None, "Job seeker"),
313|        ("PM SVANidhi", "पीएम स्वनिधि", "Ministry of Housing & Urban Affairs", "Entrepreneurs", "Central", "All India", "Working capital support for street vendors through participating lenders.", "Working capital loan and incentives subject to lender terms", "Aadhaar|Vendor certificate or survey reference|Bank details", "Approach a lending institution or apply through the official portal|Submit verification", "https://pmsvanidhi.mohua.gov.in/", "2025-01-20", None, None, None, "Entrepreneur"),
314|        ("Stand-Up India", "स्टैंड-अप इंडिया", "Department of Financial Services", "Women", "Central", "All India", "Bank loans for greenfield enterprises promoted by women and SC/ST entrepreneurs.", "Composite loan support subject to bank appraisal and scheme terms", "Identity proof|Address proof|Business plan|Category certificate where applicable", "Use the official portal|Connect with a bank|Submit project proposal", "https://www.standupmitra.in/", "2025-02-05", 18, None, None, "Entrepreneur"),
315|        ("PMAY-Gramin", "प्रधानमंत्री आवास योजना-ग्रामीण", "Ministry of Rural Development", "Housing", "Central", "All India", "Housing assistance information for eligible rural households.", "Housing assistance as per programme guidelines and local verification", "Aadhaar|Residence proof|Household details|Bank account", "Check inclusion with the Gram Panchayat|Complete verification|Follow local process", "https://pmayg.nic.in/", "2025-01-30", None, None, None, None),
316|        ("National Career Service", "राष्ट्रीय करियर सेवा", "Ministry of Labour & Employment", "Youth & Jobs", "Central", "All India", "Career discovery, counselling and job matching services for citizens.", "Job search, counselling and career resources", "Aadhaar or mobile number|Education details|Resume details", "Create a profile|Search opportunities|Apply directly where available", "https://www.ncs.gov.in/", "2025-02-08", 18, None, None, "Job seeker"),
317|        ("Beti Bachao Beti Padhao", "बेटी बचाओ बेटी पढ़ाओ", "Ministry of Women & Child Development", "Women", "Central", "All India", "Awareness and support programme promoting the rights and education of the girl child.", "Local programme support and awareness services; verify offerings locally", "Identity proof|Residence proof|School details where relevant", "Contact the district women and child development office|Verify local support", "https://wcd.nic.in/bbbp-scheme", "2025-01-18", None, None, None, None),
318|    ]
319|    for row in rows: db.add(Scheme(name=row[0], name_hi=row[1], ministry=row[2], category=row[3], level=row[4], state=row[5], summary=row[6], benefits=row[7], documents=row[8], process=row[9], source_url=row[10], verified_date=row[11], min_age=row[12], max_age=row[13], income_limit=row[14], target_occupation=row[15]))
320|    db.commit()
321|
322|
323|@app.on_event("startup")
324|def startup():
325|    db = SessionLocal()
326|    try:
327|        admin_email = os.environ.get("ADMIN_EMAIL", "admin@schemesaathi.demo")
328|        admin_password = os.environ.get("ADMIN_PASSWORD", "SchemeSaathi123!")
329|        admin = db.scalar(select(User).where(User.email == admin_email))
330|        if not admin:
331|            db.add(User(name="SchemeSaathi Admin", email=admin_email, password_hash=hash_password(admin_password), role="admin")); db.commit()
332|        elif not verify_password(admin_password, admin.password_hash):
333|            admin.password_hash = hash_password(admin_password); db.commit()
334|        seed_data(db)
335|    finally: db.close()
[End of file]
