from ml.skill_gap import analyze
from ml.recommender import career_recommendations

def test_gap_and_match():
 r=[{'skill_id':1,'name':'React','required_level':4,'weight':1}]
 a=analyze(r,{1:2}); assert a['skills'][0]['gap']==2; assert a['skills'][0]['severity']=='Medium Gap'; assert a['match']==50

def test_cosine_recommendation_is_deterministic():
 user=[{'skill_id':1,'name':'Python','level':4},{'skill_id':2,'name':'Pandas','level':3}]
 roles=[{'id':1,'name':'Data','description':'','skill_text':'Python 4 Pandas 3 Statistics 3'},{'id':2,'name':'Frontend','description':'','skill_text':'React 4 CSS 3'}]
 out=career_recommendations(user,roles); assert out[0]['name']=='Data'; assert 0<=out[0]['similarity']<=100
