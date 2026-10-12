import os
BASE_DIR=os.path.abspath(os.path.dirname(__file__))
class Config:
    SECRET_KEY=os.environ.get('SECRET_KEY','dev-change-this-secret-key')
    DATABASE=os.path.join(BASE_DIR,'skillgap.sqlite3')
    SESSION_COOKIE_HTTPONLY=True
    SESSION_COOKIE_SAMESITE='Lax'
    SESSION_COOKIE_SECURE=False
