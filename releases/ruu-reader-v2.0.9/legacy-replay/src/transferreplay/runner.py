"""Recompute archived two-family actions and exact frozen adapter eligibility.

Only trusted evaluator/adapter code is imported. Recorded submitted_code strings
are never executed. Reference diagnoses are compared after computation.
"""
from collections import Counter
from copy import deepcopy
from .local import read, sha, digest, HERE
from .tasks import task, valid_action
from .components import extract
from w04replay.runner import Comparison
from w04replay.records import write_new

PRESERVED='feasibility_preserved_by_witness'
LOST='feasibility_lost_by_certificate'
def need(ok,label):
    if not ok: raise ValueError('transfer: '+label)

def inputs():
    cases=read(HERE/'CASES.private.json');allocation=read(HERE/'ALLOCATION.json')
    paths=read(HERE/'trial-index.json')
    need(paths==[f'trials/trial-{i:02d}.json' for i in range(1,49)],'ordered numeric shards')
    trials=[read(HERE/p) for p in paths];plan=read(HERE/'PLAN.json')
    need(len(cases)==12 and len(allocation)==len(trials)==48,'fixed denominators')
    need(len({c['case_id'] for c in cases})==12,'unique cases')
    need(Counter((c['family'],c['instance']) for c in cases)==Counter({(f,i):2 for f in ['continuous','route'] for i in (1,2,3)}),'six instances/twelve histories')
    packets={}
    for c in cases:
        p=HERE/c['delivery_path'];packet=read(p)
        need(sha(p)==c['delivery_sha256'],'packet byte identity')
        need(digest(packet['history'])==c['history_sha256'],'history identity')
        need(packet['case_id']==c['case_id'] and packet['task']==task(c['family']),'case/task identity')
        n=packet['physical_step'];h=packet['history']
        need(type(n) is int and len(h['actions'])==n and len(h['states'])==n+1,'clock/history shape')
        need(packet['remaining_physical_steps']==packet['task']['physical_horizon']-n,'remaining physical clock')
        packets[c['case_id']]=packet
    for i,(a,t) in enumerate(zip(allocation,trials),1):
        need(a==t['allocation'] and a['ordinal']==i,'ordered allocation')
        r=t['result'];need(r['status']=='evaluated' and r['action_applied'] is True,'evaluated action')
        for k in ('ordinal','case_id','family','instance','state_index','profile','repeat','delivery_sha256'):
            need(r[k]==a[k],'result identity '+k)
        c=next(c for c in cases if c['case_id']==a['case_id'])
        for k in ('family','instance','state_index','delivery_path','delivery_sha256'):need(a[k]==c[k],'case/allocation '+k)
        need(a['packet_sha256']==c['delivery_sha256'],'packet binding')
        need(a['profile'] in plan['profiles'],'profile identity')
        need(type(t['action']) is dict and set(t['action'])=={'action'} and valid_action(a['family'],t['action']['action']),'legal action')
        need(len(t['analyses'])==r['analysis_calls']<=3,'analysis allowance')
        need(len(r['calls'])==r['analysis_calls']+1,'decision count')
    counts=Counter((a['case_id'],digest(a['profile']),a['repeat']) for a in allocation)
    need(counts==Counter((c['case_id'],digest(p),r) for c in cases for p in plan['profiles'] for r in (1,2)),'complete allocation factorial')
    return cases,packets,trials,plan

def adapter_report(trials,packets,plan):
    rr=[];pairs=[]
    for t in trials:
        a=t['allocation'];d=extract(t['analyses'],packets[a['case_id']],t['action']['action'])
        rr.append({k:a[k] for k in ('ordinal','case_id','profile','repeat')}|{'result_sha256':t['result_sha256']}|d)
    for cid in dict.fromkeys(t['allocation']['case_id'] for t in trials):
        for profile in plan['profiles']:
            pair=[r for r in rr if r['case_id']==cid and r['profile']==profile]
            need(len(pair)==2 and [r['repeat'] for r in pair]==[1,2],'fixed repeat pairing')
            supported=all(r['status']=='supported' for r in pair)
            # The archived panel has zero eligible pairs. Do not synthesize missing components.
            need(not supported,'unexpected supported pair requires a separately reviewed replay extension')
            pairs.append({'case_id':cid,'profile':profile,'trial_ordinals':[r['ordinal'] for r in pair],
                          'status':'unsupported','reasons':[r.get('reason') for r in pair]})
    actual={'schema':'frozen-record-intervention-v1','trial_denominator':48,'pair_denominator':24,
        'supported_trials':sum(r['status']=='supported' for r in rr),'supported_pairs':0,
        'trials':rr,'pairs':pairs,'new_model_calls':0,'part_of_live_denominator':False,
        'scope':'Counterfactual calculator rules over explicitly returned surrogate tables. Unsupported rows retained. No hidden thought reconstruction or exact mechanism attribution.'}
    need(actual==read(HERE/'INTERVENTIONS.json'),'adapter exact archive comparison')
    return actual

def negative_controls():
    from . import route
    checks=[]
    packet={'task':{'diagnostic_action_menu':[[0,0],[1,0]]}}
    table={'actions':[[0,0],[1,0]],'candidate_losses':[[0,1]],'weights':[1],'rule':'worst_case'}
    def check(name,results,final,reason):
        r=extract(results,packet,final);need(r.get('reason')==reason,name);checks.append({'check':name,'passed':True})
    check('no_analysis_is_unsupported',[],[0,0],'no_successful_analysis')
    check('missing_table_is_unsupported',[{'status':'ok','value':{}}],[0,0],'last_successful_analysis_has_no_table')
    def rows(t):return [{'status':'ok','value':{'decision_table':t}}]
    need(extract(rows(table),packet,[0,0])['status']=='supported','valid synthetic adapter reference')
    checks.append({'check':'synthetic_adapter_positive_reference_not_live_evidence','passed':True})
    changed=deepcopy(table);changed['actions'][0]=[.1,0]
    check('menu_tamper',rows(changed),[0,0],'menu_identity')
    check('final_action_mismatch',rows(table),[1,0],'rule_does_not_reproduce_final_action')
    changed=deepcopy(table);changed['weights']=[0]
    check('zero_weight_rejected',rows(changed),[0,0],'weights')
    changed=deepcopy(table);changed['candidate_losses']=[[float('nan'),1]]
    check('nonfinite_loss_rejected',rows(changed),[0,0],'finite_loss')
    changed=deepcopy(table);changed['candidate_losses']=[[0]]
    check('ragged_table_rejected',rows(changed),[0,0],'rectangular_losses')
    w={'base':[1,2,3],'offset':[0,1,2],'period':[2,3,4]}
    table=route.value_table(w);need(route.verify_table(w,table),'route certificate reference')
    table[12][0]+=1
    try:route.verify_table(w,table)
    except ValueError:checks.append({'check':'corrupted_route_value_certificate_rejected','passed':True})
    else:raise ValueError('corrupt route table accepted')
    need(not valid_action('continuous',[True,0]) and not valid_action('route',[3,0]),'illegal actions rejected')
    checks.append({'check':'illegal_action_rejected','passed':True})
    return checks

def verify(root):
    cases,packets,trials,plan=inputs()
    report=adapter_report(trials,packets,plan)
    return {'passed':True,'trials':48,'cases':12,'instances':6,'supported_trials':report['supported_trials'],
        'supported_pairs':report['supported_pairs'],'pair_denominator':24,'negative_controls':negative_controls(),
        'participant_programs_executed':0,'new_model_calls':0,'physical_transitions':0}

def reproduce(root,output):
    from .grading import grade_case
    cases,packets,trials,plan=inputs();comparison=Comparison();grades={};steps=0
    for t in trials:
        a=t['allocation'];c=next(c for c in cases if c['case_id']==a['case_id'])
        actual=grade_case(c,packets[c['case_id']],t['action'])
        comparison.compare(actual,t['grade'],'transfer/grade/'+str(a['ordinal']),exact=True)
        need(actual['diagnostic_score']==t['result']['diagnostic_score'],'grade/result verdict')
        grades[str(a['ordinal'])]=actual;steps+=actual['local_physics_steps']
    report=adapter_report(trials,packets,plan)
    rows=[]
    for family in dict.fromkeys(c['family'] for c in cases):
        for profile in plan['profiles']:
            tt=[t for t in trials if t['allocation']['family']==family and t['allocation']['profile']==profile]
            outcomes=[grades[str(t['allocation']['ordinal'])]['diagnostic_score'] for t in tt]
            pairs=[[t for t in tt if t['allocation']['case_id']==cid] for cid in dict.fromkeys(t['allocation']['case_id'] for t in tt)]
            rows.append({'family':family,'profile':profile,'denominator':12,'completed':len(tt),
                'preserved':outcomes.count(PRESERVED),'lost':outcomes.count(LOST),
                'matching_pairs':sum(len({grades[str(t['allocation']['ordinal'])]['diagnostic_score'] for t in pair})==1 for pair in pairs),
                'pair_denominator':6})
    need([(r['preserved'],r['lost'],r['matching_pairs']) for r in rows]==[(11,1,5),(11,1,5),(10,2,6),(10,2,6)],'family/profile readout')
    summary={'passed':True,'trials':48,'preserved':42,'lost':6,'unresolved_or_missing':0,'matching_pairs':22,'pair_denominator':24,
        'family_profile_rows':rows,'supported_adapter_trials':report['supported_trials'],'supported_adapter_pairs':0,
        'adapter_reasons':dict(Counter(r.get('reason','supported') for r in report['trials'])),
        'local_evaluator_steps':steps,'comparison':vars(comparison),'participant_programs_executed':0,'new_model_calls':0,
        'scope':'Archived selected actions and frozen optional-table adapter; not new live trials or universal transfer.'}
    write_new(output/'TRANSFER-GRADES.json',grades)
    write_new(output/'TRANSFER-ADAPTER.json',report)
    write_new(output/'TRANSFER-SUMMARY.json',summary)
    return summary
