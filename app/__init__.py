
from flask import Flask
from config import Config
from .database import get_db, close_db, init_schema


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    from .auth import auth, csrf_token
    from .routes import main

    app.register_blueprint(auth)
    app.register_blueprint(main)

    # Make CSRF token available to all templates
    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf_token()}

    # Initialize database tables when the application starts
    with app.app_context():
        db = get_db()
        init_schema(db)
        db.commit()

    # Close the database connection after each request
    app.teardown_appcontext(close_db)

    # Handle missing pages
    @app.errorhandler(404)
    def not_found(e):
        return "Page not found", 404

    return app
