# Project architecture

Browser → Flask routes → application services → SQLite / ML modules.

- `app/auth.py`: registration, login, logout, session and CSRF checks.
- `app/routes.py`: dashboard, skill profile, analysis, learning progress APIs.
- `app/services.py`: role analysis, dependency-aware path generation and career matching orchestration.
- `ml/skill_gap.py`: weighted proficiency gap and match calculation.
- `ml/recommender.py`: TF-IDF/cosine career similarity.
- `ml/preprocessing.py`: normalization/vector helpers.
- `data/*.csv`: seed dataset, kept outside Python logic for maintainability.
- `scripts/init_db.py`: schema + seed loader.
- `templates/`: responsive UI.
- `static/`: animation, reactive particle background and dashboard visualization.

## Runtime flow
1. User authenticates.
2. Browser submits selected skills/proficiency to `/api/skills`.
3. Target role is submitted to `/api/analyze`.
4. Services load normalized role requirements and current user skills.
5. ML gap engine computes weighted match and priorities.
6. Dependency graph is traversed for unresolved skills.
7. Resource records are attached to each learning step.
8. Completion is persisted and can increase the associated skill level by one level.
9. Fresh analysis/path data is returned to the UI.
