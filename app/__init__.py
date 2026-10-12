
import os
import csv

from flask import Flask
from werkzeug.security import generate_password_hash
from config import Config
from .database import get_db, close_db, init_schema


def seed_database(app):
    data_dir = os.path.join(app.root_path, "..", "data")

    def read_csv(filename):
        path = os.path.join(data_dir, filename)
        with open(path, newline="", encoding="utf-8") as file:
            return list(csv.DictReader(file))

    db = get_db()
    init_schema(db)

    # Add skills
    for row in read_csv("skills.csv"):
        db.execute(
            "INSERT OR IGNORE INTO skills(name, category, description) VALUES (?, ?, ?)",
            (row["name"], row["category"], row["description"])
        )

    # Add job roles
    for row in read_csv("job_roles.csv"):
        db.execute(
            "INSERT OR IGNORE INTO job_roles(name, description) VALUES (?, ?)",
            (row["name"], row["description"])
        )

    # Connect roles and required skills
    for row in read_csv("job_role_skills.csv"):
        role = db.execute(
            "SELECT id FROM job_roles WHERE name = ?", (row["role"],)
        ).fetchone()
        skill = db.execute(
            "SELECT id FROM skills WHERE name = ?", (row["skill"],)
        ).fetchone()

        if role and skill:
            db.execute(
                """INSERT OR IGNORE INTO job_role_skills
                   (job_role_id, skill_id, required_level, weight)
                   VALUES (?, ?, ?, ?)""",
                (role["id"], skill["id"],
                 int(row["required_level"]), float(row["weight"]))
            )

    # Add skill dependencies
    for row in read_csv("skill_dependencies.csv"):
        skill = db.execute(
            "SELECT id FROM skills WHERE name = ?", (row["skill"],)
        ).fetchone()
        dependency = db.execute(
            "SELECT id FROM skills WHERE name = ?", (row["depends_on"],)
        ).fetchone()

        if skill and dependency:
            db.execute(
                """INSERT OR IGNORE INTO skill_dependencies
                   (skill_id, depends_on_skill_id, strength)
                   VALUES (?, ?, ?)""",
                (skill["id"], dependency["id"], float(row["strength"]))
            )

    # Add learning resources without duplicating existing entries
    for row in read_csv("learning_resources.csv"):
        skill = db.execute(
            "SELECT id FROM skills WHERE name = ?", (row["skill"],)
        ).fetchone()

        if skill:
            exists = db.execute(
                """SELECT id FROM learning_resources
                   WHERE skill_id = ? AND title = ?""",
                (skill["id"], row["title"])
            ).fetchone()

            if not exists:
                db.execute(
                    """INSERT INTO learning_resources
                       (skill_id, title, difficulty, hours, topics,
                        practice_task, mini_project, url)
                       VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                    (skill["id"], row["title"], row["difficulty"],
                     float(row["hours"]), row["topics"],
                     row["practice_task"], row["mini_project"], row["url"])
                )

    # Create the demo account only if it doesn't already exist
    demo = db.execute(
        "SELECT id FROM users WHERE email = ?",
        ("demo@skillgap.local",)
    ).fetchone()

    if not demo:
        db.execute(
            """INSERT INTO users(name, email, password_hash)
               VALUES (?, ?, ?)""",
            (
                "Demo Student",
                "demo@skillgap.local",
                generate_password_hash("Demo@1234")
            )
        )

    db.commit()


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from .auth import auth, csrf_token
    from .routes import main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf_token()}

    app.teardown_appcontext(close_db)

    with app.app_context():
        seed_database(app)

    @app.errorhandler(404)
    def not_found(e):
        return "Page not found", 404

    return app
