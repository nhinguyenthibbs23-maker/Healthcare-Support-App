"""Exact Shapley explanation over the questionnaire topics (works for any scikit-learn pipeline).

With only a handful of questions every coalition can be enumerated, so no approximation is needed.
Contributions are on the probability scale and add up to: estimate for this person - average estimate
of a background sample of training answers. They describe associations in the survey model, not causes.
"""
from itertools import combinations
from math import factorial
import numpy as np,pandas as pd
from utils.data_loader import SPECS

def shapley(pipeline,values,m):
    features=list(m['features']);n=len(features);bg=pd.DataFrame(m['explanation']['background'],columns=features).astype(float);k=len(bg)
    x=pd.Series({f:float(values[f]) for f in features})
    masks=[frozenset(s) for r in range(n+1) for s in combinations(range(n),r)]
    frames=[]
    for s in masks:
        frame=bg.copy()
        for i in s: frame[features[i]]=x[features[i]]
        frames.append(frame)
    prob=pipeline.predict_proba(pd.concat(frames,ignore_index=True))[:,1].reshape(len(masks),k).mean(axis=1)
    value=dict(zip(masks,prob));phi=np.zeros(n)
    for i in range(n):
        for s in masks:
            if i in s: continue
            w=factorial(len(s))*factorial(n-len(s)-1)/factorial(n);phi[i]+=w*(value[s|{i}]-value[s])
    return dict(zip(features,phi)),float(value[frozenset()]),float(value[frozenset(range(n))])

def explain(pipeline,values,m):
    phi,base,total=shapley(pipeline,values,m)
    rows=[{'Factor':SPECS[f][0],'Feature':f,'Contribution':float(v),'Direction':'Raises estimate' if v>0 else 'Lowers estimate' if v<0 else 'Neutral'} for f,v in phi.items()]
    r=pd.DataFrame(rows);r=r.iloc[np.argsort(-abs(r.Contribution.to_numpy()))]
    r.attrs['base']=base;r.attrs['total']=total
    desc='Exact Shapley contributions on the probability scale relative to the average training answer (%.1f%%). They add up to your estimate. Associations, not causes.'%(base*100)
    return r,desc
