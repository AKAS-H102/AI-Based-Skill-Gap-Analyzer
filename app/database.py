import sqlite3
from flask import current_app, g

def get_db():
    if 'db' not in g:
        g.db=sqlite3.connect(current_app.config['DATABASE'])
        g.db.row_factory=sqlite3.Row
        g.db.execute('PRAGMA foreign_keys=ON')
    return g.db

def close_db(e=None):
    db=g.pop('db',None)
    if db: db.close()

def init_schema(db):
    db.executescript('''
    CREATE TABLE IF NOT EXISTS users(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, email TEXT UNIQUE NOT NULL, password_hash TEXT NOT NULL, created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS skills(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, category TEXT, description TEXT);
    CREATE TABLE IF NOT EXISTS job_roles(id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT UNIQUE NOT NULL, description TEXT);
    CREATE TABLE IF NOT EXISTS job_role_skills(job_role_id INTEGER NOT NULL, skill_id INTEGER NOT NULL, required_level INTEGER NOT NULL, weight REAL NOT NULL DEFAULT 1, PRIMARY KEY(job_role_id,skill_id), FOREIGN KEY(job_role_id) REFERENCES job_roles(id) ON DELETE CASCADE, FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS user_skills(user_id INTEGER NOT NULL, skill_id INTEGER NOT NULL, level INTEGER NOT NULL CHECK(level BETWEEN 1 AND 4), PRIMARY KEY(user_id,skill_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS learning_resources(id INTEGER PRIMARY KEY AUTOINCREMENT, skill_id INTEGER NOT NULL, title TEXT NOT NULL, difficulty TEXT NOT NULL, hours REAL NOT NULL, topics TEXT NOT NULL, practice_task TEXT NOT NULL, mini_project TEXT NOT NULL, url TEXT NOT NULL, FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS skill_dependencies(skill_id INTEGER NOT NULL, depends_on_skill_id INTEGER NOT NULL, strength REAL NOT NULL DEFAULT 1, PRIMARY KEY(skill_id,depends_on_skill_id), FOREIGN KEY(skill_id) REFERENCES skills(id) ON DELETE CASCADE, FOREIGN KEY(depends_on_skill_id) REFERENCES skills(id) ON DELETE CASCADE);
    CREATE TABLE IF NOT EXISTS learning_progress(id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL, resource_id INTEGER NOT NULL, completed INTEGER NOT NULL DEFAULT 0, progress INTEGER NOT NULL DEFAULT 0 CHECK(progress BETWEEN 0 AND 100), updated_at TEXT DEFAULT CURRENT_TIMESTAMP, UNIQUE(user_id,resource_id), FOREIGN KEY(user_id) REFERENCES users(id) ON DELETE CASCADE, FOREIGN KEY(resource_id) REFERENCES learning_resources(id) ON DELETE CASCADE);
    CREATE INDEX IF NOT EXISTS idx_user_skills_user ON user_skills(user_id);
    CREATE INDEX IF NOT EXISTS idx_role_skills_role ON job_role_skills(job_role_id);
    CREATE INDEX IF NOT EXISTS idx_progress_user ON learning_progress(user_id);
    ''')
