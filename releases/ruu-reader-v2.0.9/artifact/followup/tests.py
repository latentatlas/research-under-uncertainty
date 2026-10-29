"""Authored contract controls and counterexamples on copied reader inputs.

No saved evidence is modified and no participant/physics/provider code runs.
"""
from pathlib import Path
import copy,hashlib,importlib.util,json
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('followup_source_check',H/'source_check.py')
s=importlib.util.module_from_spec(spec);spec.loader.exec_module(s)
B='B_required_model';A='A_optional_model';C='C_required_executor'

def main():
    checks=[]
    def positive(name,condition):
        assert condition,name;checks.append({'case':name,'passed':True,'expected':'accepted_with_expected_result'})
    def reject(name,fn,code):
        try:fn()
        except ValueError as e:
            assert code in str(e),(name,str(e),code)
            checks.append({'case':name,'passed':True,'expected':'rejected','error_code':str(e)})
        else:raise AssertionError('not_rejected:'+name)
    ctx={'case_id':'authored-control','menu':[[0],[1]]};ctx['menu_sha256']=s.digest(ctx['menu'])
    def wire(table='[[0,1]]',rule='uniform_mean',action=0,**changes):
        r={'schema':'executable-decision-record-v1','case_id':ctx['case_id'],'menu_sha256':ctx['menu_sha256'],'loss_definition_id':'remaining_task_failure_forecast_v1','candidate_losses':'__TABLE__','rule':rule};r.update(changes)
        return json.dumps({'decision':{'action_id':action,'record':r}},separators=(',',':')).replace('"__TABLE__"',table)
    positive('valid_one_row',s.derive_final(wire(),B,ctx)['record_diagnostics']['single_row'])
    positive('decimal_precision_not_float_tie',s.derive_final(wire('[[0.5000000000000000000000000000000000001,0.5]]',action=1),B,ctx)['record_selected_action_id']==1)
    positive('ties_first_index',s.derive_final(wire('[[0.5,0.5]]'),B,ctx)['record_selected_action_id']==0)
    two=s.derive_final(wire('[[0,1],[1,0.2]]'),B,ctx)
    three=s.derive_final(wire('[[0,1],[1,0.2],[1,0.2]]',action=1),B,ctx)
    positive('duplicate_multiplicity_retained',two['record_selected_action_id']==0 and three['record_selected_action_id']==1 and three['record_diagnostics']['duplicate_rows']==1)
    control=s.derive_final(wire('[[0,0.6],[0.8,0.6]]'),B,ctx)
    positive('supported_rules_can_disagree',control['record_diagnostics']['rule_actions']=={'uniform_mean':0,'worst_case':1})
    positive('B_conflicting_proposal_still_executed',s.derive_final(wire(action=1),B,ctx)['executed_action_id']==1)
    positive('C_selects_record_when_proposal_conflicts',s.derive_final(wire(action=1),C,ctx)['executed_action_id']==0)
    positive('A_missing_record_undefined',s.derive_final('{"decision":{"action_id":0}}',A,ctx)['record_action_agreement'] is None)
    invalid_optional=s.derive_final(wire(rule='unsupported'),A,ctx)
    positive('A_invalid_record_does_not_invent_validity',invalid_optional['record_valid'] is False and invalid_optional['executed_action_id']==0 and invalid_optional['record_error']=='unsupported_rule')
    for name,raw,code in [
        ('wrong_case',wire(case_id='other'),'record_identity'),
        ('wrong_record_menu',wire(menu_sha256='0'*64),'record_identity'),
        ('unsupported_rule',wire(rule='other'),'unsupported_rule'),
        ('ragged_table',wire('[[0]]'),'rectangular_losses'),
        ('string_number',wire('[["0",1]]'),'loss_range_or_type'),
        ('out_of_range_forecast',wire('[[-0.01,1]]'),'loss_range_or_type'),
        ('boolean_action',wire(action=True),'action_id'),
        ('out_of_menu_action',wire(action=2),'action_id'),
        ('duplicate_key',wire().replace('"action_id":0','"action_id":0,"action_id":1'),'duplicate_key'),
        ('nonfinite_number',wire('[[NaN,1]]'),'nonfinite_number'),
        ('exponent_limit',wire('[[1e-101,1]]'),'numeric_exponent_or_finiteness'),
        ('B_missing_record','{"decision":{"action_id":0}}','required_record:absent')]:
        reject(name,lambda raw=raw:s.derive_final(raw,B,ctx),code)
    wrong_context=copy.deepcopy(ctx);wrong_context['menu'][0]=[7]
    reject('menu_bytes_do_not_match_hash',lambda:s.derive_final(wire(),B,wrong_context),'context_menu_binding')

    def load(n):return json.loads((H/n).read_text())
    trials=load('trials.json')['trials'];allocation=load('allocation.json');index=load('final-index.json')
    menus=json.loads((H.parent/'data/crossing.json').read_text())
    raw={e['file']:(H/e['file']).read_bytes() for e in index['entries']}
    baseline=s.verify_inputs(trials,allocation,index,menus,raw.__getitem__)
    positive('all_31_tables_and_46_labels',baseline['numeric_tables_recomputed']==31 and baseline['menu_label_bindings_verified']==46)
    # These controls call the derivation directly, rather than relying on MANIFEST rejection.
    t=copy.deepcopy(trials);t[0]['label']='L' if t[0]['label']=='P' else 'P'
    reject('wrong_trial_label_detected',lambda:s.verify_inputs(t,allocation,index,menus,raw.__getitem__),'bound_menu_label')
    m=copy.deepcopy(menus);r=next(t for t in trials if t['status']=='completed');case=r['allocation']['case_id'];a=r['decision']['executed_action_id']
    m['labelmaps'][case]['labels'][a]='L' if r['label']=='P' else 'P'
    reject('wrong_census_label_detected',lambda:s.verify_inputs(trials,allocation,index,m,raw.__getitem__),'bound_menu_label')
    m=copy.deepcopy(menus);m['labelmaps'][case]['menu_sha256']='0'*64
    reject('label_bound_to_wrong_menu',lambda:s.verify_inputs(trials,allocation,index,m,raw.__getitem__),'label_menu_identity')
    t=copy.deepcopy(trials);target=next(t for t in t if t['decision'] and t['decision']['record_valid']);target['decision']['record_diagnostics']['rows']+=1
    reject('precomputed_diagnostic_cannot_override_table',lambda:s.verify_inputs(t,allocation,index,menus,raw.__getitem__),'source_derived_decision_mismatch')
    idx=copy.deepcopy(index);idx['entries'][0]['trial_id']='wrong-trial'
    reject('final_bound_to_wrong_trial',lambda:s.verify_inputs(trials,allocation,idx,menus,raw.__getitem__),'final_trial_identity')
    # Rebind edited test bytes in the copied index so hash checks do not hide the semantic check.
    idx=copy.deepcopy(index);edited=dict(raw);entry=next(e for e in idx['entries'] if e['contains_record'])
    obj=json.loads(edited[entry['file']]);obj['decision']['record']['candidate_losses']=[[1-v for v in row] for row in obj['decision']['record']['candidate_losses']]
    edited[entry['file']]=json.dumps(obj,separators=(',',':')).encode();h=hashlib.sha256(edited[entry['file']]).hexdigest();entry['sha256']=entry['source_sha256']=h
    reject('changed_table_with_rebound_test_hash',lambda:s.verify_inputs(trials,allocation,idx,menus,edited.__getitem__),'source_derived_decision_mismatch')
    return {'passed':True,'controls':checks,'positive_controls':sum(c['expected']=='accepted_with_expected_result' for c in checks),'negative_controls':sum(c['expected']=='rejected' for c in checks),'new_model_calls':0,'new_physics_runs':0,'archived_files_modified':False,'independent_human_or_laboratory_validation':False}

if __name__=='__main__':print(json.dumps(main(),sort_keys=True))
