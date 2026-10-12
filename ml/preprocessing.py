import re
def normalize(text): return re.sub(r'[^a-z0-9+#. ]+',' ',str(text).lower()).strip()
def skill_vector(skills): return {int(s['skill_id']):int(s['level']) for s in skills}
