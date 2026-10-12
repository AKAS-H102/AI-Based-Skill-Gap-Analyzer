import pandas as pd
LEVELS={1:'Beginner',2:'Intermediate',3:'Advanced',4:'Expert'}
def analyze(required,current):
    rows=[]; total=weighted=0
    for r in required:
        cur=int(current.get(r['skill_id'],0)); req=int(r['required_level']); gap=max(req-cur,0); w=float(r['weight']); total+=req*w; weighted+=min(cur,req)*w
        if cur>=req: cls='strong'
        elif cur>0: cls='partial'
        else: cls='missing'
        severity='No Gap' if gap==0 else ('Low Gap' if gap==1 else ('Medium Gap' if gap==2 else 'High Gap'))
        priority=(gap*w)
        rows.append({**dict(r),'current_level':cur,'current_label':LEVELS.get(cur,'Not assessed'),'required_label':LEVELS[req],'gap':gap,'classification':cls,'severity':severity,'priority':round(priority,2)})
    score=round((weighted/total*100) if total else 0,1)
    return {'match':score,'skills':sorted(rows,key=lambda x:(-x['priority'],-x['weight']))}
