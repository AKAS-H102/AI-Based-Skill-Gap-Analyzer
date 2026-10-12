import os,tempfile
import pytest
from app import create_app
from app.database import get_db,init_schema
from werkzeug.security import generate_password_hash
@pytest.fixture()
def client(tmp_path):
 app=create_app(); app.config.update(TESTING=True,DATABASE=str(tmp_path/'test.sqlite3'),SECRET_KEY='test')
 with app.app_context():
  db=get_db(); init_schema(db); db.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',('Test','test@example.com',generate_password_hash('Password1!'))); db.commit()
 with app.test_client() as c: yield c

def test_login_and_protected(client):
 r=client.get('/dashboard'); assert r.status_code==302
 with client.session_transaction() as s: s['csrf']='abc'
 r=client.post('/login',data={'email':'test@example.com','password':'Password1!','csrf_token':'abc'}); assert r.status_code==302
 r=client.get('/dashboard'); assert r.status_code==200
