"""Fixed pilot counterexample through conditional task labels. No participant/model.
Twelve existing plans/actions and five selectors; present-host numerical replay,
not new collection, independent implementation or historical attestation.
"""
from pathlib import Path
from copy import deepcopy
import hashlib,json,math,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'legacy-replay/src'))
from w04replay import components,grading,physics
from w04replay.records import digest,read
from w04replay.snapshot_core import validate_packet,verify_bounds,verdict,score_action
METRICS=('total_cost','target_max','target_mean_square','path_peak','terminal_norm')
COUNTS={'A1':8,'A2':4}
LABELS={'feasibility_preserved_by_witness':'preserved','feasibility_lost_by_certificate':'lost','unresolved':'unresolved'}
def need(v,label):
    if not v:raise ValueError(label)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def close(a,b):return type(a) in (int,float) and type(b) in (int,float) and math.isfinite(a) and math.isfinite(b) and abs(a-b)<=1e-8*(1+abs(b))
def pair(v):return type(v) is list and len(v)==2 and all(close(x,x) for x in v)
def compare(actual,expected,path='grade'):
    """Exact discrete fields/shapes; stated tolerance for numeric trace replay."""
    if type(expected) is dict:
        need(type(actual) is dict and set(actual)==set(expected),path+':keys')
        for k in expected:compare(actual[k],expected[k],path+'/'+k)
    elif type(expected) is list:
        need(type(actual) is list and len(actual)==len(expected),path+':length')
        for i,x in enumerate(expected):compare(actual[i],x,path+'/'+str(i))
    elif type(expected) is float:need(type(actual) is float and close(actual,expected),path+':numeric')
    else:need(type(actual) is type(expected) and actual==expected,path+':exact')
def load_sources(root=H.parent):
    bindings=read(root/'artifact/source/pilot-sensitivity-bindings.json')
    for name,h in bindings['files'].items():
        p=Path(name);need(not p.is_absolute() and '..' not in p.parts,'source_path')
        need(sha(root/p)==h,'source_hash:'+name)
    data=read(root/'legacy-replay/data/component_inputs.json');cases=read(root/'legacy-replay/data/cases.json')
    saved=read(root/'artifact/source/pilot-sensitivity.private.json')
    lock=read(root/'artifact/source/pilot-sensitivity-actions-lock.json');grades=read(root/'artifact/source/pilot-sensitivity-grades.json')
    need(sha(root/'artifact/source/pilot-sensitivity-grades.json')==saved['grade_file_sha256'],'original_grade_file_hash')
    need(sha(root/'artifact/source/pilot-sensitivity-actions-lock.json')==saved['actions_lock_sha256'],'original_action_lock_hash')
    return data,cases['boundary-01'],saved,lock,grades,bindings

def index_records(saved,lock,grades):
    expected={(p,i) for p,n in COUNTS.items() for i in range(n)}
    need(len(saved['records'])==len(lock['records'])==12,'record_count')
    rows={(r['pool'],r['candidate_index']):r for r in saved['records']};locked={(r['pool'],r['candidate_index']):r for r in lock['records']}
    need(set(rows)==set(locked)==expected,'unique_pool_index_identity')
    need(lock['physical_grading_started'] is False and lock['historical_outcomes_already_known'] is True,'retrospective_lock_scope')
    keys=set()
    for key,row in rows.items():
        need(pair(row['action']),'finite_action_shape');need(digest(row['action'])==row['action_sha256'],'action_hash')
        need(set(row['metrics'])==set(METRICS),'metric_set')
        need({k:row[k] for k in locked[key]}==locked[key],'action_lock_row');keys.add(row['action_sha256'])
    need(len(keys)==12 and set(grades)==keys,'exact_grade_action_set')
    need([r['selector'] for r in saved['selectors']]==list(METRICS),'selector_order')
    need([r['selector'] for r in lock['selectors']]==list(METRICS),'locked_selector_order')
    for row,before in zip(saved['selectors'],lock['selectors']):need({k:row[k] for k in before}==before,'selector_lock')
    return rows

def evidence_label(g,bundle,action):
    """Bind supplied witness/certificate to this case, prefix and applied action."""
    case=bundle['case'];n=case['after_step'];validate_packet(bundle['packet'],case)
    need(case['case_id']==g['case_id']=='boundary-01','grade_case_identity')
    need(bundle['world_sha256']==digest(bundle['world']),'grade_world_identity')
    need(pair(action) and pair(g['applied_action']),'grade_action_shape')
    applied=physics.validate_action(action)
    need(g['applied_action']==[applied.real,applied.imag],'grade_applied_action')
    for name,step in [('before',n),('after',n+1)]:
        a=g[name];result=a['witness_result'];trace=result['trajectory'];cert=a['certificate']
        need(a['after_step']==step and len(trace)>=step,'evidence_clock')
        need(result['world']==bundle['world'] and result['world_sha256']==bundle['world_sha256'],'witness_world_identity')
        need(trace[:n]==bundle['source_trace'],'witness_history_identity');need(result['steps']==len(trace),'witness_length')
        need([t['step'] for t in trace]==list(range(1,len(trace)+1)),'witness_step_order')
        if name=='after':need(trace[n]['action']==g['applied_action'],'witness_action_identity')
        if cert.get('certified') and cert.get('method')=='fixed_positive_projection':
            need(cert['after_step']==step,'certificate_clock')
            need(cert['initial_state']==trace[step-1]['private_after'][:2],'certificate_state_identity')
            need(verify_bounds(cert),'certificate_arithmetic')
        success=physics.score(result['status'],[t['radius'] for t in trace])
        need(success is result['success_005'] and a['witness_success'] is (success is True),'witness_success_binding')
        need(a['verdict']==verdict(a['witness_success'],cert['certified']),'evidence_verdict')
    need(g['before']['verdict']=='reachable_by_witness','feasible_before')
    score=score_action(g['before'],g['after'])
    need(score==g['diagnostic_score'] and score in LABELS,'diagnosis_evidence_binding')
    return LABELS[score]

def recompute_plans(data,bundle,rows):
    history=data['boundary01_history'];state=history['states'][-1];n=len(history['actions'])
    need(history==bundle['packet']['history'] and n==bundle['case']['after_step']==11,'plan_history_identity')
    vals=data['values']
    pools={'A1':[{**deepcopy(m),'family':'t4','id':f't4-{i}','C':m['drift_coef']} for i,m in enumerate(vals['4']['models'][:8])],
           'A2':[{**deepcopy(m),'family':'t6','id':f't6-{i}'} for i,m in enumerate(vals['6']['models'])]}
    need({p:len(ms) for p,ms in pools.items()}==COUNTS,'pool_counts')
    components.calls={'candidate_step_evaluations':0,'optimizer_invocations':0,'new_llm_requests':0,'parameter_refits':0,'physical_steps':0}
    computed={};maximum_error=0.0
    for pool,models in pools.items():
        for i,model in enumerate(models):
            plan=components.optimize([model],state,n,1000);targets=plan['candidate_target_norms'][0]
            metrics={'total_cost':plan['cost'],'target_max':max(targets),'target_mean_square':sum(x*x for x in targets)/len(targets),
                     'path_peak':plan['candidate_max_norms'][0],'terminal_norm':targets[-1]}
            original=rows[pool,i];need(original['candidate_id']==model['id'],'candidate_identity')
            for key,value in metrics.items():
                need(close(value,original['metrics'][key]),'metric:'+pool+':'+str(i)+':'+key)
                maximum_error=max(maximum_error,abs(value-original['metrics'][key]))
            need(pair(plan['first_action']) and all(close(a,b) for a,b in zip(plan['first_action'],original['action'])),'first_action')
            computed[pool,i]={'metrics':metrics,'action':plan['first_action']}
    return computed,maximum_error

def verify_grade_replay(bundle,row,computed,archived):
    archived_label=evidence_label(archived,bundle,row['action'])
    need(row['diagnosis']==archived_label,'archived_record_label')
    need(row['applied_action']==archived['applied_action'],'record_applied_action')
    actual=grading.grade(bundle,computed['action']);label=evidence_label(actual,bundle,computed['action'])
    compare(actual,archived);need(label==archived_label,'replayed_label')
    return actual,label

def select(data,saved,computed):
    selectors=[]
    for ref in saved['selectors']:
        metric=ref['selector'];indices={p:min(range(n),key=lambda i:(computed[p,i]['metrics'][metric],i)) for p,n in COUNTS.items()}
        labels={p:computed[p,i]['replayed_diagnosis'] for p,i in indices.items()}
        distance=math.dist(data['actions']['6'],computed['A2',indices['A2']]['action'])
        need(indices==ref['selected_indices'] and labels==ref['diagnoses'],'selector:'+metric)
        need(ref['native_compatible'] is True and distance<=1e-6 and close(distance,ref['native_action_distance']),'native_compatibility')
        selectors.append({'selector':metric,'selected_indices':indices,'native_action_distance':distance,'replayed_diagnoses':labels,
                          'crossed_action_norm':math.hypot(*computed['A1',indices['A1']]['action'])})
    return selectors

def run(return_context=False):
    data,bundle,saved,lock,grades,bindings=load_sources();rows=index_records(saved,lock,grades)
    computed,maximum_error=recompute_plans(data,bundle,rows);actual_grades={};evidence=[];steps=0
    for key,row in rows.items():
        archived=grades[row['action_sha256']]['grade'];actual,label=verify_grade_replay(bundle,row,computed[key],archived)
        actual_grades[key]=actual;computed[key]['replayed_diagnosis']=label;steps+=actual['local_physics_steps']
        evidence.append({'pool':key[0],'candidate_index':key[1],'diagnosis':label,'stored_grade_pointer':'/'+row['action_sha256']+'/grade',
                         'full_grade_compared':True,'witness_success':actual['after']['witness_success'],
                         'certificate_method':actual['after']['certificate'].get('method'),'certificate_certified':actual['after']['certificate']['certified']})
    result={'passed':True,'plans_recomputed':len(computed),'selectors_recomputed':select(data,saved,computed),'grade_records_replayed':len(actual_grades),
            'grade_evidence':evidence,'maximum_metric_abs_error':maximum_error,'numeric_tolerance':'abs(a-b) <= 1e-8*(1+abs(b))','native_action_tolerance':1e-6,
            'source_sha256':bindings['files'],'original_grade_file_sha256':saved['grade_file_sha256'],'plan_work':components.calls,
            'verification_grader_calls':len(actual_grades),'verification_local_physics_transitions':steps,'task_labels_recomputed_on_present_host':True,
            'label_scope':'Existing conditional grader; full archived witnesses/certificates bound and compared. Uniform library proof and historical runtime attestation remain open.',
            'participant_programs_executed':0,'new_model_calls':0,'new_scientific_samples':0,'uniform_library_proof':False,'historical_runtime_attestation':False,
            'independent_implementation':False,'independent_laboratory':False}
    need((H.parent/'paper/table-pilot-sensitivity.tex').read_text()==render_table(result),'manuscript_sensitivity_table')
    return (result,(data,bundle,saved,lock,grades,rows,computed,actual_grades)) if return_context else result

def render_table(report):
    names=['Total penalized cost (R2*)','Maximum target-step norm','Mean squared target-step norm','Trajectory peak norm','Final-step norm']
    label={'preserved':'P','lost':'L','unresolved':'U'}
    rows=[]
    for name,s in zip(names,report['selectors_recomputed']):
        a=s['selected_indices'];d=s['replayed_diagnoses']
        rows.append(f"{name} & {a['A2']}/{label[d['A2']]} & {a['A1']}/{label[d['A1']]} & {s['crossed_action_norm']:.6f}"+r'\\')
    return '\n'.join([r'\begin{table}[htbp]',r'\centering\small',r'\begin{tabular}{lccr}\toprule',
        r'Criterion minimized & Native A2: plan/label & Crossed A1: plan/label & Action norm\\\midrule',*rows,r'\bottomrule\end{tabular}',
        r'\caption{Pilot context B: five selectors applied to the same fixed plan pools.',
        r'Indices are zero-based. All five select native A2 plan 2 and reproduce the',
        r'original action within $10^{-6}$. The first three select the same crossed',
        r'A1 plan; the minimum-peak selector instead selects plan 3, giving L rather',
        r'than P. Norms refer to crossed actions. Labels retain the conditional',
        r'continuous evaluation premises. These five selectors are not independent',
        r'replications or a probability sample of completions.}',r'\label{tab:b-completions}',r'\end{table}',''])
if __name__=='__main__':print(json.dumps(run(),sort_keys=True))
