"""Derive source decisions and recount the closed follow-up. No model, physics or participant-code execution."""
from pathlib import Path
from collections import Counter, defaultdict
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import importlib.util

H=Path(__file__).resolve().parent
MODELS=('gpt-6-astra','gpt-6.1-sol')
ARMS=('A_optional_model','B_required_model','C_required_executor')

def ensure(condition, name):
    if not condition: raise ValueError(name)

def summarize(trials):
    ensure(len(trials)==48,'48_original_slots')
    ensure([x['allocation']['order'] for x in trials]==list(range(1,49)),'ordered_slots')
    ensure(len({x['allocation']['trial_id'] for x in trials})==48,'unique_trial_ids')
    ensure([x['allocation']['order'] for x in trials if x['status']=='technical']==[13,14],'preserved_technical_slots')
    blocks=defaultdict(list)
    for x in trials:
        a=x['allocation'];d=x['decision'];diag=d.get('record_diagnostics') if d else None
        ensure(a['model'] in MODELS and a['arm'] in ARMS,'profile_arm')
        ensure(a['profile']=={'mode':'single_agent','model':a['model'],'reasoning_effort':'max','service_tier':'fast'},'fixed_profile')
        ensure(x['status'] in ('completed','technical','protocol'),'status')
        ensure(x['full_task_success_measured'] is False and x['mock_only'] is False,'scope_flags')
        ensure(1<=x['model_requests']<=4 and 0<=x['analyses']<=3 and 0<=x['analysis_errors']<=x['analyses'],'resource_counts')
        ensure(x['segment']==(1 if a['order']<=13 else 2 if a['order']==14 else 3),'segment_identity')
        if x['status']=='technical':
            ensure(d is None and x['label'] is None,'technical_not_scientific_loss')
        if x['status']=='completed':
            ensure(x['label'] in ('P','L','U') and d is not None,'completed_label')
            ensure(d['arm']==a['arm'] and d['case_id']==a['case_id'] and d['menu_sha256']==a['menu_sha256'],'decision_identity')
            external=a['arm']==ARMS[2]
            ensure(d['external_execution_agreement_by_construction']==external,'construction_flag')
            ensure(d['executed_action_id']==d['record_selected_action_id'] if external else d['executed_action_id']==d['proposed_action_id'],'execution_contract')
            if a['arm']!=ARMS[0]: ensure(d['record_valid'] is True,'required_valid_record')
            if d['record_valid']:
                ensure(diag is not None,'diagnostics_present')
                ensure(d['record_action_agreement']==(d['record_selected_action_id']==d['proposed_action_id']),'observed_correspondence')
                ensure(diag['rows']>=1 and 1<=diag['distinct_numeric_rows']<=diag['rows'],'row_counts')
                ensure(diag['single_row']==(diag['rows']==1),'single_row_flag')
                ensure(diag['duplicate_rows']==diag['rows']-diag['distinct_numeric_rows'],'duplicate_rows')
                ensure(set(diag['rule_actions'])=={'uniform_mean','worst_case'},'supported_rules')
                ensure(diag['rules_choose_same_action']==(len(set(diag['rule_actions'].values()))==1),'same_action_flag')
                ensure(diag['hypothesis_semantics_verified'] is False,'no_semantic_attestation')
            else:
                ensure(diag is None and d['record_action_agreement'] is None,'absent_record_undefined')
        blocks[a['block_id']].append(x)
    ensure(len(blocks)==16,'triplet_count')
    for block in blocks.values():
        ensure(len(block)==3 and {x['allocation']['arm'] for x in block}==set(ARMS),'triplet_arms')
        for key in ('model','case_id','repeat','profile_sha256','menu_sha256','packet_sha256'):
            ensure(len({x['allocation'][key] for x in block})==1,'triplet_identity_'+key)
    profiles={}
    for model in MODELS:
        rows=[x for x in trials if x['allocation']['model']==model]
        ensure(len(rows)==24,'24_slots_per_model')
        arms={}
        for arm in ARMS:
            sub=[x for x in rows if x['allocation']['arm']==arm]
            valid=[x for x in sub if x['decision'] and x['decision']['record_valid']]
            arms[arm]={
                'planned':8,'recorded':len(sub),'status_counts':dict(Counter(x['status'] for x in sub)),
                'labels':dict(Counter(x['label'] for x in sub if x['label'] is not None)),
                'valid_record_denominator':len(valid),
                'record_proposal_matches':sum(x['decision']['record_action_agreement'] for x in valid),
                'single_row_records':sum(x['decision']['record_diagnostics']['single_row'] for x in valid),
                'records_with_duplicate_rows':sum(x['decision']['record_diagnostics']['duplicate_rows']>0 for x in valid),
                'same_rule_action_records':sum(x['decision']['record_diagnostics']['rules_choose_same_action'] for x in valid),
                'execution_agreement_by_construction':arm==ARMS[2],
            }
        mb=[b for b in blocks.values() if b[0]['allocation']['model']==model]
        pairs={}
        for left,right in zip(ARMS,ARMS[1:]):
            observed=[]
            for block in mb:
                byarm={x['allocation']['arm']:x for x in block};a,b=byarm[left],byarm[right]
                if a['status']!='technical' and b['status']!='technical':
                    observed.append(int(b['label']=='P')-int(a['label']=='P'))
            n=len(observed);net=sum(observed)
            pairs[left+'__'+right]={
                'planned_pairs':8,'observed_pairs':n,'missing_or_technical_pairs':8-n,
                'right_minus_left_net':net,'difference':float(Fraction(net,n)) if n else None,
                'difference_fraction':str(Fraction(net,n)) if n else None,
                'gains':observed.count(1),'losses':observed.count(-1),'ties':observed.count(0)}
        profiles[model]={'arms':arms,'pairs':pairs,
            'completed_triplets':sum(all(x['status']=='completed' for x in b) for b in mb),
            'planned_partial_triplets':sum(len(b)!=3 for b in mb),
            'scientifically_incomplete_triplets':sum(not all(x['status']=='completed' for x in b) for b in mb),
            'triplets_with_technical_loss':sum(any(x['status']=='technical' for x in b) for b in mb),
            'started':len(rows),'real_unstarted':24-len(rows),'active':0,
            'analyses':sum(x['analyses'] for x in rows),'analysis_errors':sum(x['analysis_errors'] for x in rows),
            'C_conflicting_proposals':sum(x['decision']['proposed_action_id']!=x['decision']['record_selected_action_id'] for x in rows if x['allocation']['arm']==ARMS[2] and x['decision'])}
    return profiles

def verify():
    def read(name):return json.loads((H/name).read_text())
    for name,sha in read('SOURCE-BINDINGS.json')['selected_files'].items():
        ensure(hashlib.sha256((H/name).read_bytes()).hexdigest()==sha,'projection_hash_'+name)
    spec=importlib.util.spec_from_file_location('followup_source_check',H/'source_check.py')
    source=importlib.util.module_from_spec(spec);spec.loader.exec_module(source)
    derived=source.verify()
    for name,sha in read('SOURCE-BINDINGS.json')['shared_files'].items():
        ensure(hashlib.sha256((H/name).read_bytes()).hexdigest()==sha,'shared_file_hash_'+name)
    trials=read('trials.json')['trials'];profiles=summarize(trials)
    reference=read('reference.json')
    ensure(reference['pooled_primary_inference'] is False and reference['full_task_success_measured'] is False,'reference_scope')
    for model,p in profiles.items():
        expected=reference['profiles'][model]
        ensure(p['arms']==expected['arms'],'arm_aggregate_'+model)
        ensure(p['planned_partial_triplets']==expected['partial_triplets']==expected['planned_partial_triplets'],'planned_partial_triplets')
        ensure(p['completed_triplets']==expected['fully_scientifically_completed_triplets'],'scientific_complete_triplets')
        for k in ('scientifically_incomplete_triplets','triplets_with_technical_loss'):
            ensure(p[k]==expected[k],k)
        for key,fields in p['pairs'].items():
            ensure(all(fields[k]==v for k,v in expected['pairs'][key].items() if k!='interpretation'),'paired_aggregate_'+model)
    accounting=read('accounting.json'); combined=accounting['combined_operational_only']
    for model,usage in accounting['by_model'].items():
        rows=[x for x in trials if x['allocation']['model']==model]
        ensure(sum(x['model_requests'] for x in rows)==usage['requests'],'requests_'+model)
        ensure(usage['known_usage_requests']+usage['unknown_usage_requests']==usage['requests'],'usage_partition')
        ensure(usage['cached_input_tokens']<=usage['input_tokens'],'cache_is_subset')
        ensure(usage['cache_split_assessed_requests']==usage['known_usage_requests'],'cache_assessed_population')
        ensure(usage['usage_unknown_requests_excluded_from_cache_split']==usage['unknown_usage_requests'],'cache_excluded_population')
        ensure(0<=usage['cache_split_unknown_requests']<=usage['cache_split_assessed_requests'],'unknown_cache_known_usage_only')
        ensure(usage['unknown_input_reserve']==usage['unknown_usage_requests']*1050000,'input_reserve')
        ensure(usage['unknown_output_reserve']==usage['unknown_usage_requests']*128000,'output_reserve')
    for key in ('requests','known_usage_requests','unknown_usage_requests','input_tokens','cached_input_tokens','output_tokens','unknown_input_reserve','unknown_output_reserve','cache_split_assessed_requests','usage_unknown_requests_excluded_from_cache_split','cache_split_unknown_requests'):
        ensure(sum(v[key] for v in accounting['by_model'].values())==combined[key],'combined_usage_'+key)
    for key in ('measured_credit_equivalent','unknown_reserve_credit_equivalent'):
        ensure(sum(Decimal(v[key]) for v in accounting['by_model'].values())==Decimal(combined[key]),'combined_credit_'+key)
    ensure(Decimal(combined['measured_credit_equivalent'])+Decimal(combined['unknown_reserve_credit_equivalent'])<=Decimal(accounting['original_local_credit_equivalent_limit']),'local_bound')
    return {'passed':True,'scope':'exact final-table derivation, menu/label binding and scalar recount; no physical replay','profiles':profiles,
            'original_assignments':48,'completed':46,'technical':2,'protocol':0,'active':0,'real_unstarted':0,
            'full_task_success_measured':False,'pooled_primary_inference':False,
            'new_model_calls':0,'new_physics_runs':0,'raw_table_diagnostics_recomputed':True,'source_derivation':derived,
            'usage':'Archived receipt totals checked arithmetically; receipts not regenerated or independently attested.'}

if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
