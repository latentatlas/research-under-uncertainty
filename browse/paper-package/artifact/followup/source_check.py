"""Derive follow-up decisions from exact final JSON, then bind actions to menus.

Independent reader implementation of the published numeric contract. Standard
library only: no runtime imports, participant programs, physics or provider calls.
"""
from decimal import Decimal, InvalidOperation
from fractions import Fraction
from pathlib import Path
import hashlib
import json

RULES=('uniform_mean','worst_case')
ARMS=('A_optional_model','B_required_model','C_required_executor')

def ensure(condition,code):
    if not condition: raise ValueError(code)

def digest(value):
    return hashlib.sha256(json.dumps(value,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False).encode()).hexdigest()

def unique_pairs(pairs):
    d={}
    for k,v in pairs:
        ensure(k not in d,'duplicate_key');d[k]=v
    return d

def reject_constant(_): raise ValueError('nonfinite_number')

def number(token):
    ensure(len(token)<=80,'numeric_lexeme_limit')
    try: d=Decimal(token)
    except InvalidOperation: raise ValueError('invalid_number') from None
    ensure(d.is_finite() and abs(d.as_tuple().exponent)<=100,'numeric_exponent_or_finiteness')
    return Fraction(d)

DECODER=json.JSONDecoder(object_pairs_hook=unique_pairs,parse_int=number,parse_float=number,parse_constant=reject_constant)

def field_text(text,field):
    """Return original JSON value lexemes, without float conversion/serialization."""
    obj=DECODER.decode(text)
    ensure(type(obj) is dict and field in obj,'missing_field')
    i=text.index('{')+1
    while True:
        while text[i].isspace(): i+=1
        key,i=DECODER.raw_decode(text,i)
        while text[i].isspace(): i+=1
        ensure(text[i]==':','field_colon');i+=1
        while text[i].isspace(): i+=1
        start=i;_,i=DECODER.raw_decode(text,i)
        if key==field:return text[start:i]
        while text[i].isspace(): i+=1
        ensure(text[i]==',','field_separator');i+=1

def context_length(context):
    ensure(type(context) is dict and set(context)=={'case_id','menu','menu_sha256'},'context_schema')
    ensure(type(context['case_id']) is str and type(context['menu']) is list and len(context['menu'])>0,'context_identity')
    ensure(digest(context['menu'])==context['menu_sha256'],'context_menu_binding')
    return len(context['menu'])

def record_selection(record,context):
    n=context_length(context)
    ensure(type(record) is dict and set(record)=={'schema','case_id','menu_sha256','loss_definition_id','candidate_losses','rule'},'record_fields')
    ensure(record['schema']=='executable-decision-record-v1' and record['loss_definition_id']=='remaining_task_failure_forecast_v1','record_version_or_loss')
    ensure(record['case_id']==context['case_id'] and record['menu_sha256']==context['menu_sha256'],'record_identity')
    ensure(record['rule'] in RULES,'unsupported_rule')
    table=record['candidate_losses']
    ensure(type(table) is list and 1<=len(table)<=128,'row_count')
    ensure(all(type(r) is list and len(r)==n for r in table),'rectangular_losses')
    ensure(all(type(v) is Fraction and 0<=v<=1 for r in table for v in r),'loss_range_or_type')
    rows=tuple(tuple(r) for r in table)
    actions={}
    for rule in RULES:
        scores=[sum((r[j] for r in rows),Fraction())/len(rows) if rule=='uniform_mean' else max(r[j] for r in rows) for j in range(n)]
        actions[rule]=min(range(n),key=lambda j:(scores[j],j))
    diagnostics={
        'rows':len(rows),'distinct_numeric_rows':len(set(rows)),
        'duplicate_rows':len(rows)-len(set(rows)),'single_row':len(rows)==1,
        'distinct_argmin_sets':len({tuple(j for j,v in enumerate(r) if v==min(r)) for r in rows}),
        'rules_choose_same_action':len(set(actions.values()))==1,
        'rule_actions':actions,'hypothesis_semantics_verified':False}
    return actions[record['rule']],diagnostics

def derive_final(wire_text,arm,context):
    n=context_length(context)
    ensure(arm in ARMS,'arm')
    ensure(type(wire_text) is str and len(wire_text.encode())<=1048576,'wire_size')
    wire=DECODER.decode(wire_text)
    ensure(type(wire) is dict and set(wire)=={'decision'},'wire_fields')
    text=field_text(wire_text,'decision')
    ensure(len(text.encode())<=262144,'submission_size_or_type')
    final=wire['decision']
    ensure(type(final) is dict and set(final) in ({'action_id'},{'action_id','record'}),'common_final_fields')
    proposed=final['action_id']
    ensure(type(proposed) is Fraction and proposed.denominator==1 and 0<=proposed<n,'action_id')
    proposed=int(proposed);selected=None;diagnostics=None;error=None
    if 'record' in final:
        try:selected,diagnostics=record_selection(final['record'],context)
        except ValueError as exc:error=str(exc)
    ensure(arm==ARMS[0] or diagnostics is not None,'required_record:'+(error or 'absent'))
    executed=selected if arm==ARMS[2] else proposed
    return {
        'arm':arm,'case_id':context['case_id'],'menu_sha256':context['menu_sha256'],
        'proposed_action_id':proposed,'executed_action_id':executed,
        'record_valid':diagnostics is not None,'record_error':error,
        'record_selected_action_id':selected,
        'record_action_agreement':selected==proposed if diagnostics is not None else None,
        'external_execution_agreement_by_construction':arm==ARMS[2],
        'record_diagnostics':diagnostics,
        'raw_submission_sha256':hashlib.sha256(text.encode()).hexdigest()}

def verify_inputs(trials,allocation,index,menu_source,read_final):
    ensure([t['allocation'] for t in trials]==allocation['rows'],'original_allocation_identity')
    ensure([t['allocation']['order'] for t in trials]==list(range(1,49)),'original_order')
    completed=[t for t in trials if t['status']=='completed']
    ensure([e['order'] for e in index['entries']]==[t['allocation']['order'] for t in completed],'final_index_orders')
    ensure(index['technical_without_final']==[13,14],'technical_final_absence')
    bound={e['order']:e for e in index['entries']}
    ensure(len(bound)==len(completed)==46,'46_unique_final_sources')
    contexts=menu_source['contexts'];labelmaps=menu_source['labelmaps']
    tables=0;matches=0;by_model={};derived_trials=[]
    for trial in trials:
        a=trial['allocation'];d=trial['decision'];ctx=contexts[a['case_id']]
        n=context_length(ctx)
        ensure(ctx['case_id']==a['case_id'] and ctx['menu_sha256']==a['menu_sha256'],'allocation_menu_identity')
        ensure(digest(a['profile'])==a['profile_sha256'],'profile_hash')
        lm=labelmaps[a['case_id']]
        ensure(lm['case_id']==a['case_id'] and lm['menu_sha256']==ctx['menu_sha256'],'label_menu_identity')
        ensure(type(lm['labels']) is list and len(lm['labels'])==n and all(l in ('P','L','U') for l in lm['labels']),'label_shape')
        if trial['status']!='completed':
            ensure(d is None and trial['label'] is None and a['order'] not in bound,'noncompleted_not_labeled')
            continue
        entry=bound[a['order']]
        ensure(entry['trial_id']==a['trial_id'],'final_trial_identity')
        ensure(entry['file']==f"finals/trial-{a['order']:03d}.json",'final_path_identity')
        raw=read_final(entry['file'])
        ensure(hashlib.sha256(raw).hexdigest()==entry['sha256']==entry['source_sha256'],'source_final_bytes')
        computed=derive_final(raw.decode('utf-8'),a['arm'],ctx)
        ensure(computed==d,'source_derived_decision_mismatch')
        ensure(computed['raw_submission_sha256']==entry['inner_final_sha256'],'inner_final_bytes')
        commit={'trial_id':a['trial_id'],'profile_sha256':a['profile_sha256'],'decision':computed}
        ensure(hashlib.sha256((json.dumps(commit,sort_keys=True,separators=(',',':'),ensure_ascii=False)+'\n').encode()).hexdigest()==trial['decision_sha256'],'decision_commit_hash')
        action=computed['executed_action_id']
        ensure(type(action) is int and 0<=action<n,'executed_menu_index')
        ensure(lm['labels'][action]==trial['label'],'bound_menu_label')
        ensure(entry['contains_record']==computed['record_valid'],'source_record_presence')
        tables+=computed['record_valid'];matches+=1
        model=by_model.setdefault(a['model'],{'finals':0,'tables':0,'labels_bound':0,'B_valid':0,'B_matches':0,'B_same_rule':0,'C_conflicting_proposals':0})
        model['finals']+=1;model['labels_bound']+=1;model['tables']+=computed['record_valid']
        if a['arm']==ARMS[1]:
            model['B_valid']+=computed['record_valid'];model['B_matches']+=computed['record_action_agreement'] is True
            model['B_same_rule']+=computed['record_diagnostics']['rules_choose_same_action']
        if a['arm']==ARMS[2]:model['C_conflicting_proposals']+=computed['proposed_action_id']!=computed['record_selected_action_id']
        derived_trials.append({'order':a['order'],'declared_rule':DECODER.decode(raw.decode())['decision'].get('record',{}).get('rule'),'record_valid':computed['record_valid'],'record_selected_action_id':computed['record_selected_action_id'],'executed_action_id':action,'label_from_bound_menu':lm['labels'][action]})
    ensure(tables==index['record_tables']==31,'31_source_tables')
    return {'passed':True,'final_responses_reparsed':matches,'numeric_tables_recomputed':tables,'menu_label_bindings_verified':matches,
            'by_model':by_model,'per_trial_derivations':derived_trials,
            'physics_regraded':False,'provider_responses_regenerated':False,'independent_historical_attestation':False,
            'scope':'Reparse exact minimal finals, derive validity/declared and alternative rule choices/diagnostics, compare preserved decisions, and look up labels in the existing bound menu census.'}

def verify():
    h=Path(__file__).resolve().parent
    def read(p):return json.loads(p.read_text(),object_pairs_hook=unique_pairs,parse_constant=reject_constant)
    return verify_inputs(read(h/'trials.json')['trials'],read(h/'allocation.json'),read(h/'final-index.json'),read(h.parent/'data/crossing.json'),lambda p:(h/p).read_bytes())

if __name__=='__main__':print(json.dumps(verify(),sort_keys=True))
