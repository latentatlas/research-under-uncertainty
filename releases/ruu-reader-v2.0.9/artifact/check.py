"""Offline reader check of projected records and registered paired statistics.

No environment, actor, participant program, network or model invocation.
"""
from pathlib import Path
from collections import Counter
import json,hashlib,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
import paired_statistics as ps

def need(ok,code):
    if not ok:raise ValueError(code)
def read(p):return json.loads(p.read_text())
def manifest_check(root):
    expected=read(root/'MANIFEST.json')['files']
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file() and p!=root/'MANIFEST.json'}
    need(actual==set(expected),'manifest_file_set')
    for name,h in expected.items():
        p=root/name
        need(not p.is_symlink() and hashlib.sha256(p.read_bytes()).hexdigest()==h,'manifest_hash:'+name)
    return len(actual)

def acquisition(rows):
    need([x['trial_id'] for x in rows]==[f't{i:04d}' for i in range(1,5001)],'ordered_5000_identities')
    cells=Counter();wrong=0;diagnostics=Counter();work={a:Counter() for a in ('fixed','adaptive')}
    for x in rows:
        a=x['arms']['adaptive'];f=x['arms']['fixed']
        for name,r in x['arms'].items():
            need(r['trial_id']==x['trial_id'] and r['arm']==name and r['exited'] is True,'arm_identity_exit')
            need(type(r['certificate']) is bool and r['query_id'] in ('q0','q1'),'record_contract')
            need(r['compatible_after']>0 and r['target_values'],'nonempty_compatible_set')
            need(r['certificate']==(len(r['target_values'])==1),'unanimity_certificate')
            need(r['prediction']==(r['target_values'][0] if r['certificate'] else None),'prediction_binding')
            need(x['environment_work']['extra_observations'][name]==1,'equal_observation_budget')
            need(all(type(v) is int and v>=0 for v in r['work'].values()),'complete_integer_work')
            if name=='fixed':need(r['pre_observation_query_evaluations']==0 and r['query_id']=='q0','fixed_no_selection_scan')
            wrong+=int(r['certificate'] and r['prediction']!=x['truth'])
            work[name].update(r['work'])
        cells[f"n{int(a['certificate'])}{int(f['certificate'])}"]+=1
        diagnostics['initially_ambiguous']+=a['initial_target_cardinality']>1
        diagnostics['initially_singleton']+=a['initial_target_cardinality']==1
        diagnostics['query_disagreement']+=a['query_id']!=f['query_id']
        p=a['possible_gain_loss']
        diagnostics['possible_gain']+=p['gain_possible']
        diagnostics['possible_loss']+=p['loss_possible']
        diagnostics['realized_gain_with_possible_gain']+=a['certificate'] and not f['certificate'] and p['gain_possible']
        diagnostics['realized_loss_with_possible_loss']+=f['certificate'] and not a['certificate'] and p['loss_possible']
    cells={k:cells[k] for k in ('n00','n01','n10','n11')}
    verdict=ps.decision(5000,cells['n11'],cells['n10'],cells['n01'],cells['n00'],wrong_certificates=wrong)
    return {'cells':cells,'wrong_certificates':wrong,'decision':verdict,'diagnostics':dict(diagnostics),
            'work':{a:dict(c) for a,c in work.items()}}

def scientific_checks():
    import crossing_check as cc
    cross,detail=cc.reconstruct()
    ref=read(H/'data/crossing-reference.json')
    for key in ('conditions','historical_transfer','pilot'):
        need(cross[key]==ref[key],'crossing_reference:'+key)
    controls=cc.controls()
    sys.path.insert(0,str(H/'acquisition'))
    from loader import project_records
    rows=project_records()
    acq=acquisition(rows);aref=read(H/'data/acquisition-reference.json')
    for key in ('cells','wrong_certificates','decision','diagnostics','work'):
        need(acq[key]==aref[key],'acquisition_reference:'+key)
    # These controls test validity and denominator boundaries, not fresh worlds.
    need(ps.decision(5000,282,90,1,4627,wrong_certificates=1)['status']=='invalid_certificate_hold','wrong_certificate_preempts_interval')
    need(ps.directional_status(0,0)=='inconclusive','empty_discordance_not_success')
    need(ps.extra_work_per_net_certificate(10,1,1) is None,'zero_net_gain_no_cost_ratio')
    return {'passed':True,'crossing_conditions':cross['conditions'],'acquisition':acq,
      'synthetic_controls':controls+['wrong_certificate_preempts_interval','empty_discordance_not_success','zero_net_gain_no_cost_ratio'],
      'new_model_calls':0,'new_observations':0,'participant_programs':0,'physical_labels_recomputed':False}

if __name__=='__main__':
    count=manifest_check(H.parent)
    result=scientific_checks()
    # Compact public result; full detailed tables remain reproducible from data.
    print(json.dumps({'passed':result['passed'],'manifest_files':count,
        'mandatory_pair_count':result['crossing_conditions']['executable_record']['eligible_pairs'],
        'full_additional_cells_beyond_scan':result['crossing_conditions']['executable_record']['full_additional_cells_beyond_record_scan'],
        'acquisition_cells':result['acquisition']['cells'],'interval':result['acquisition']['decision']['interval']['delta'],
        'wrong_certificates':result['acquisition']['wrong_certificates'],
        'controls':len(result['synthetic_controls']),'new_model_calls':0,'new_observations':0},sort_keys=True))
