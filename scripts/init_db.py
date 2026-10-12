import os,sys,csv,sqlite3
sys.path.insert(0,os.path.dirname(os.path.dirname(__file__)))
from app import create_app
from app.database import get_db,init_schema
from werkzeug.security import generate_password_hash
app=create_app()
with app.app_context():
    db=get_db(); init_schema(db)
    def rows(file):
        with open(os.path.join(os.path.dirname(__file__),'..','data',file),newline='',encoding='utf8') as f:return list(csv.DictReader(f))
    for r in rows('skills.csv'): db.execute('INSERT OR IGNORE INTO skills(name,category,description) VALUES(?,?,?)',(r['name'],r['category'],r['description']))
    for r in rows('job_roles.csv'): db.execute('INSERT OR IGNORE INTO job_roles(name,description) VALUES(?,?)',(r['name'],r['description']))
    for r in rows('job_role_skills.csv'):
        rid=db.execute('SELECT id FROM job_roles WHERE name=?',(r['role'],)).fetchone()[0]; sid=db.execute('SELECT id FROM skills WHERE name=?',(r['skill'],)).fetchone()[0]; db.execute('INSERT OR REPLACE INTO job_role_skills VALUES(?,?,?,?)',(rid,sid,int(r['required_level']),float(r['weight'])))
    for r in rows('skill_dependencies.csv'):
        a=db.execute('SELECT id FROM skills WHERE name=?',(r['skill'],)).fetchone(); b=db.execute('SELECT id FROM skills WHERE name=?',(r['depends_on'],)).fetchone()
        if a and b: db.execute('INSERT OR REPLACE INTO skill_dependencies VALUES(?,?,?)',(a[0],b[0],float(r['strength'])))
    for r in rows('learning_resources.csv'):
        sid=db.execute('SELECT id FROM skills WHERE name=?',(r['skill'],)).fetchone()[0]; db.execute('INSERT INTO learning_resources(skill_id,title,difficulty,hours,topics,practice_task,mini_project,url) VALUES(?,?,?,?,?,?,?,?)',(sid,r['title'],r['difficulty'],float(r['hours']),r['topics'],r['practice_task'],r['mini_project'],r['url']))
    db.execute("INSERT OR IGNORE INTO users(name,email,password_hash) VALUES(?,?,?)",('Demo Student','demo@skillgap.local',generate_password_hash('Demo@1234')))
    db.commit(); print('Database initialized. Demo login: demo@skillgap.local / Demo@1234')
