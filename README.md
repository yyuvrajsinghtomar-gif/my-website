I’ll retrieve the current `README.md` and provide the complete project documentation.
Action: view_file({"path":"/app/README.md","view_range":[1,1000]})
Observation: [Showing lines 1-18 of 18 total] /app/README.md:
1|# SchemeSaathi
2|
3|SchemeSaathi is a responsive government scheme discovery and eligibility checker for India. It includes a React frontend, FastAPI REST API, JWT email/password authentication, relational SQLAlchemy models, saved schemes, profile-based rule checks, and an admin catalogue view.
4|
5|## Run locally
6|
7|1. Install backend dependencies with `pip install -r backend/requirements.txt`.
8|2. Install frontend dependencies with `cd frontend && yarn`.
9|3. Start the backend through the workspace supervisor on port 8001 and the frontend with `yarn start`.
10|4. The local development `.env` uses SQLite so the starter runs immediately. For PostgreSQL, set `DATABASE_URL` to a PostgreSQL SQLAlchemy connection URL and restart the backend.
11|
12|## Demo admin
13|
14|Email: `admin@schemesaathi.demo`  
15|Password: `SchemeSaathi123!`
16|
17|All sample schemes are clearly presented as demo information. Users should verify current eligibility, deadlines, benefits, and application requirements on each official source URL.
18|
[End of file]
