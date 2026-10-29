"""Frozen numeric table adapter; no prose inference or archived code execution."""
import math
from .local import digest

def select(table,rule):
    losses=table['candidate_losses'];weights=table['weights'];n=len(table['actions'])
    if rule=='weighted_mean':scores=[sum(w*r[j] for w,r in zip(weights,losses))/sum(weights) for j in range(n)]
    elif rule=='worst_case':scores=[max(r[j] for r in losses) for j in range(n)]
    else:raise ValueError('unsupported rule')
    if not all(math.isfinite(x) for x in scores):raise ValueError('nonfinite rule result')
    i=min(range(n),key=lambda j:(scores[j],j))
    return table['actions'][i]

def extract(results,packet,final):
    successful=[r for r in results if r.get('status')=='ok']
    if not successful:return {'status':'unsupported','reason':'no_successful_analysis'}
    value=successful[-1].get('value')
    if type(value) is not dict or 'decision_table' not in value:return {'status':'unsupported','reason':'last_successful_analysis_has_no_table'}
    t=value['decision_table']
    try:
        if type(t) is not dict or set(t)!={'actions','candidate_losses','weights','rule'}:raise ValueError('table_schema')
        if digest(t['actions'])!=digest(packet['task']['diagnostic_action_menu']):raise ValueError('menu_identity')
        L=t['candidate_losses'];w=t['weights'];n=len(t['actions'])
        if type(L) is not list or not 1<=len(L)<=128 or type(w) is not list or len(w)!=len(L):raise ValueError('candidate_count')
        if any(type(r) is not list or len(r)!=n for r in L):raise ValueError('rectangular_losses')
        if any(type(x) not in (int,float) or not math.isfinite(x) or abs(x)>1e100 for r in L for x in r):raise ValueError('finite_loss')
        if any(type(x) not in (int,float) or not math.isfinite(x) or not 0<=x<=1e100 for x in w) or sum(w)<=0:raise ValueError('weights')
        chosen=select(t,t['rule'])
        if max(abs(x-y) for x,y in zip(chosen,final))>1e-8:raise ValueError('rule_does_not_reproduce_final_action')
    except (ValueError,KeyError,TypeError,OverflowError) as e:return {'status':'unsupported','reason':str(e)}
    return {'status':'supported','table':t,'table_sha256':digest(t),'scope':'explicit participant numeric surrogate, not true dynamics or hidden reasoning'}

def crossing(t1,t2):
    if digest(t1['actions'])!=digest(t2['actions']):raise ValueError('cross menu identity')
    return [{'pool_repeat':i+1,'rule_repeat':j+1,'rule':rule['rule'],'action':select(pool,rule['rule'])} for i,pool in enumerate((t1,t2)) for j,rule in enumerate((t1,t2))]
