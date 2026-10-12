import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

def career_recommendations(user_skills, roles, limit=5):
    user_text=' '.join([f"{x['name']} "*max(1,int(x['level'])) for x in user_skills])
    corpus=[user_text]+[r['skill_text'] for r in roles]
    mat=TfidfVectorizer(ngram_range=(1,2)).fit_transform(corpus)
    scores=cosine_similarity(mat[0:1],mat[1:]).ravel()
    out=[]
    for r,s in zip(roles,scores): out.append({'id':r['id'],'name':r['name'],'description':r['description'],'similarity':round(float(s*100),1)})
    return sorted(out,key=lambda x:-x['similarity'])[:limit]
