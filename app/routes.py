from flask import Blueprint,render_template,request,jsonify,session,redirect,url_for,current_app
from .database import get_db
from .auth import login_required,check_csrf
from .services import role_analysis,learning_path,career_matches

main=Blueprint('main',__name__)
@main.get('/')
def index(): return redirect(url_for('main.dashboard')) if session.get('user_id') else redirect(url_for('auth.login'))
@main.get('/dashboard')
@login_required
def dashboard():
    db=get_db(); roles=db.execute('SELECT * FROM job_roles ORDER BY name').fetchall(); skills=db.execute('SELECT * FROM skills ORDER BY category,name').fetchall(); selected={r['skill_id']:r['level'] for r in db.execute('SELECT skill_id,level FROM user_skills WHERE user_id=?',(session['user_id'],)).fetchall()}; return render_template('dashboard.html',roles=roles,skills=skills,selected=selected)
@main.get('/api/roles/<int:role_id>/skills')
@login_required
def role_skills(role_id):
    return jsonify(role_analysis(session['user_id'],role_id))
@main.post('/api/skills')
@login_required
def save_skills():
    if not check_csrf(): return jsonify(error='Invalid CSRF token'),400
    data=request.get_json(silent=True) or {}; items=data.get('skills',[]); db=get_db()
    for x in items:
        sid=int(x.get('skill_id')); level=max(1,min(4,int(x.get('level',1))))
        if not db.execute('SELECT id FROM skills WHERE id=?',(sid,)).fetchone(): continue
        db.execute('INSERT INTO user_skills(user_id,skill_id,level) VALUES(?,?,?) ON CONFLICT(user_id,skill_id) DO UPDATE SET level=excluded.level',(session['user_id'],sid,level))
    db.commit(); return jsonify(ok=True)
@main.post('/api/analyze')
@login_required
def analyze_api():
    if not check_csrf(): return jsonify(error='Your session token expired. Refresh the page and try again.'),400
    data=request.get_json(silent=True) or {}
    try:
        role_id=int(data.get('role_id',0))
        if role_id<=0: return jsonify(error='Please choose a target career role.'),400
        if not get_db().execute('SELECT id FROM job_roles WHERE id=?',(role_id,)).fetchone():
            return jsonify(error='That career role was not found. Refresh the page and choose another role.'),404
        analysis=role_analysis(session['user_id'],role_id)
        path=learning_path(session['user_id'],role_id)
        careers=career_matches(session['user_id'])
        return jsonify(analysis|{'path':path,'careers':careers})
    except Exception:
        current_app.logger.exception('Skill gap analysis failed for user_id=%s',session.get('user_id'))
        return jsonify(error='The analysis could not be completed. Check the Flask terminal for the detailed error, then retry.'),500
@main.get('/api/path/<int:role_id>')
@login_required
def path_api(role_id): return jsonify(path=learning_path(session['user_id'],role_id))
@main.post('/api/progress')
@login_required
def progress():
    if not check_csrf(): return jsonify(error='Invalid CSRF token'),400
    data=request.get_json(silent=True) or {}; rid=int(data.get('resource_id')); value=max(0,min(100,int(data.get('progress',0)))); done=1 if value>=100 else 0; db=get_db()
    db.execute('''INSERT INTO learning_progress(user_id,resource_id,progress,completed) VALUES(?,?,?,?) ON CONFLICT(user_id,resource_id) DO UPDATE SET progress=excluded.progress,completed=excluded.completed,updated_at=CURRENT_TIMESTAMP''',(session['user_id'],rid,value,done))
    if done:
        row=db.execute('SELECT skill_id FROM learning_resources WHERE id=?',(rid,)).fetchone()
        if row:
            sid=row['skill_id']; db.execute('INSERT INTO user_skills(user_id,skill_id,level) VALUES(?,?,1) ON CONFLICT(user_id,skill_id) DO UPDATE SET level=MIN(level+1,4)',(session['user_id'],sid))
    db.commit()
    role_id=int(data.get('role_id',0) or 0)
    payload={'ok':True,'progress':value,'completed':bool(done)}
    if role_id: payload.update(role_analysis(session['user_id'],role_id)); payload['path']=learning_path(session['user_id'],role_id)
    return jsonify(payload)
@main.get('/profile')
@login_required
def profile():
    db=get_db(); u=db.execute('SELECT * FROM users WHERE id=?',(session['user_id'],)).fetchone(); skills=db.execute('SELECT s.*,u.level FROM user_skills u JOIN skills s ON s.id=u.skill_id WHERE u.user_id=? ORDER BY s.name',(session['user_id'],)).fetchall(); return render_template('profile.html',user=u,skills=skills)
