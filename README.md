# AI-Based Skill Gap Analyzer and Learning Path Generator

A production-style college project implementing a real, data-driven career intelligence platform with Flask, SQLite and Python ML.

## Features
- Registration/login/logout with password hashing, sessions and CSRF protection.
- 34 seeded technical skills and 10 career roles.
- Weighted skill-gap analysis using proficiency levels 1–4.
- Strong / partial / missing classification and low/medium/high gap severity.
- TF-IDF + cosine similarity career recommendations.
- Dependency-aware learning-path generation from the SQLite graph.
- Curated learning resources with topics, practice tasks, mini projects and URLs.
- Progress tracking that persists in SQLite.
- Animated analysis sequence, charts, reactive particles, responsive glass UI and reduced-motion support.
- Automated tests for core ML logic and HTTP flows.

## Architecture
`routes.py` handles HTTP/UI/API; `services.py` contains application logic; `ml/` contains matching/recommendation/gap algorithms; `database.py` owns SQLite connections/schema; CSV files provide seed data.

## Database schema
`users`, `skills`, `job_roles`, `job_role_skills`, `user_skills`, `learning_resources`, `skill_dependencies`, `learning_progress`. Foreign keys and indexes are enabled.

## AI/ML methodology
### Weighted skill matching
For every required skill:
`gap = max(required_level - current_level, 0)`.
The score is:
`sum(min(current_level, required_level) * weight) / sum(required_level * weight) * 100`.
This prevents over-proficiency from inflating a role match.

### Career recommendation
The user's skill profile is converted into weighted text (repeated by proficiency). Each job role's required skills form another document. Scikit-learn TF-IDF vectors and cosine similarity produce deterministic career similarity scores.

### Learning path
Only unresolved gaps are considered. Dependency edges are inspected first, then the target skill. Already-covered skills are skipped. The engine chooses a resource for each unresolved learning target and includes persisted completion state.

## Setup (Windows)
```text
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
python scripts/init_db.py
python run.py
```
Open `http://127.0.0.1:5000`.

Demo credentials: `demo@skillgap.local` / `Demo@1234`

## Testing
```text
pytest -q
```

## Viva questions and answers
1. **Why weighted matching?** Important skills should influence a role score more than incidental skills.
2. **Why cap current level at required level?** Expert knowledge should not compensate for unrelated missing skills.
3. **Why TF-IDF?** It provides a transparent vector representation for comparing user skill profiles with role skill descriptions.
4. **Why cosine similarity?** It measures the directional similarity of sparse skill vectors independent of absolute document length.
5. **Why dependencies?** Learning prerequisites in order avoids recommending advanced topics before foundational ones.
6. **Where is the model?** The ML logic is implemented in Python with scikit-learn; the system is not a random/static recommendation list.
7. **Why SQLite?** It is lightweight, relational and appropriate for a local college project while still supporting normalized relationships.
8. **How is security handled?** Password hashes, server sessions, CSRF checks, validation and parameterized SQL are used.

## Future enhancements
- Replace curated resources with a periodically refreshed public-resource catalog.
- Add semantic embeddings for richer role/profile matching.
- Add resume parsing and skill extraction.
- Add instructor/admin analytics.
- Add PostgreSQL deployment and background model jobs.


## Troubleshooting

If you see `TypeError: Object of type Undefined is not JSON serializable` on `/dashboard`, ensure you are using the latest project version. The CSRF token is injected at application scope so `base.html` can safely serialize it with Jinja `tojson` on every route.
