from flask import Flask
from config import Config
from .database import get_db,close_db

def create_app():
    app=Flask(__name__); app.config.from_object(Config)
    from .auth import auth, csrf_token
    from .routes import main
    app.register_blueprint(auth); app.register_blueprint(main)
    # CSRF token is needed by templates rendered from every blueprint.
    # Register it at application scope instead of only on the auth blueprint.
    @app.context_processor
    def inject_csrf_token():
        return {"csrf_token": csrf_token()}
    app.teardown_appcontext(close_db)
    @app.errorhandler(404)
    def not_found(e): return ('Page not found',404)
    return app
