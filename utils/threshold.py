import numpy as np
import pandas as pd
from sklearn.metrics import roc_curve

def threshold_table(y,p):
    y,p=np.asarray(y,dtype=int),np.asarray(p,dtype=float)
    fpr,tpr,t=roc_curve(y,p,drop_intermediate=False);t=np.where(np.isinf(t),np.nextafter(1.,2.),t)
    tp=np.rint(tpr*sum(y==1)).astype(int);fp=np.rint(fpr*sum(y==0)).astype(int);fn=sum(y==1)-tp;tn=sum(y==0)-fp
    precision=np.divide(tp,tp+fp,out=np.zeros_like(tp,dtype=float),where=(tp+fp)>0)
    f1=np.divide(2*tp,2*tp+fp+fn,out=np.zeros_like(tp,dtype=float),where=(2*tp+fp+fn)>0)
    return pd.DataFrame(dict(threshold=t,TP=tp,FP=fp,FN=fn,TN=tn,precision=precision,recall=tpr,F1=f1,FPR=fpr,alerts=tp+fp))

def choose_threshold(table,c_fp,c_fn):
    if not np.isfinite([c_fp,c_fn]).all() or min(c_fp,c_fn)<0 or c_fp+c_fn<=0: raise ValueError('Costs must be finite, nonnegative, and at least one positive.')
    result=table.copy();result['total_cost']=c_fp*result.FP+c_fn*result.FN
    result['cost_per_person']=result.total_cost/int(result.iloc[0][['TP','FP','FN','TN']].sum())
    best=result.sort_values(['total_cost','FN','threshold'],ascending=[True,True,False]).iloc[0]
    return best,result
