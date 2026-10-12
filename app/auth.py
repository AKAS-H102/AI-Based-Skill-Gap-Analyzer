import secrets
from functools import wraps
from flask import Blueprint, request, session, redirect, url_for, render_template, flash, jsonify
from werkzeug.security import generate_password_hash, check_password_hash
from .database import get_db

auth=Blueprint('auth',__name__)

def csrf_token():
    if 'csrf' not in session: session['csrf']=secrets.token_urlsafe(32)
    return session['csrf']

def login_required(fn):
    @wraps(fn)
    def wrapped(*a,**kw):
        if not session.get('user_id'):
            if request.path.startswith('/api/'): return jsonify(error='Authentication required'),401
            return redirect(url_for('auth.login'))
        return fn(*a,**kw)
    return wrapped

def check_csrf():
    token=request.form.get('csrf_token') or request.headers.get('X-CSRFToken')
    return token and secrets.compare_digest(token,session.get('csrf',''))

@auth.route('/register',methods=['GET','POST'])
def register():
    if request.method=='POST':
        name=request.form.get('name','').strip(); email=request.form.get('email','').strip().lower(); pw=request.form.get('password','')
        if not check_csrf(): flash('Security check failed. Please retry.','danger')
        elif len(name)<2 or '@' not in email or len(pw)<8: flash('Enter a valid name, email and password of at least 8 characters.','danger')
        else:
            db=get_db()
            try:
                db.execute('INSERT INTO users(name,email,password_hash) VALUES(?,?,?)',(name,email,generate_password_hash(pw))); db.commit(); flash('Account created. Please sign in.','success'); return redirect(url_for('auth.login'))
            except Exception: flash('That email is already registered.','danger')
    return render_template('auth.html',mode='register')

@auth.route('/login',methods=['GET','POST'])
def login():
    if request.method=='POST':
        if not check_csrf(): flash('Security check failed.','danger')
        else:
            row=get_db().execute('SELECT * FROM users WHERE email=?',(request.form.get('email','').strip().lower(),)).fetchone()
            if row and check_password_hash(row['password_hash'],request.form.get('password','')):
                session.clear(); session['user_id']=row['id']; session['user_name']=row['name']; session['csrf']=secrets.token_urlsafe(32); return redirect(url_for('main.dashboard'))
            flash('Invalid email or password.','danger')
    return render_template('auth.html',mode='login')

@auth.post('/logout')
def logout():
    if check_csrf(): session.clear()
    return redirect(url_for('auth.login'))
