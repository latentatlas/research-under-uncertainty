"""Fault tests on copied in-memory evidence and a removed temporary source tree."""
from pathlib import Path
from copy import deepcopy
import json,sys,tempfile,shutil
sys.path.insert(0,str(Path(__file__).resolve().parent))
import pilot_sensitivity as s

def main():
    report,ctx=s.run(return_context=True)
    data,bundle,saved,lock,grades,rows,computed,actual=ctx
    checks=[]
    def rejects(name,fragment,call):
        try:call()
        except ValueError as e:
            s.need(fragment in str(e),'unexpected_rejection:'+name+':'+str(e))
            checks.append({'test':name,'passed':True,'rejection':str(e)})
        else:raise AssertionError('accepted_corruption:'+name)
    row=rows['A1',2];g=grades[row['action_sha256']]['grade']
    x=deepcopy(g);x['case_id']='boundary-02'
    rejects('same_label_wrong_case','grade_case_identity',lambda:s.evidence_label(x,bundle,row['action']))
    x=deepcopy(g);x['applied_action'][0]+=0.001
    rejects('wrong_applied_action','grade_applied_action',lambda:s.evidence_label(x,bundle,row['action']))
    x=deepcopy(g);x['after']['witness_result']=deepcopy(actual['A1',0]['after']['witness_result'])
    rejects('borrowed_positive_witness','witness_action_identity',lambda:s.evidence_label(x,bundle,row['action']))
    lossrow=rows['A1',3];loss=deepcopy(grades[lossrow['action_sha256']]['grade'])
    loss['after']['certificate']['bounds'][-1]+=0.01
    rejects('corrupt_negative_bound','rational/Decimal mismatch',lambda:s.evidence_label(loss,bundle,lossrow['action']))
    loss=deepcopy(grades[lossrow['action_sha256']]['grade']);loss['after']['certificate']['initial_state'][0]+=0.001
    rejects('certificate_for_other_state','certificate_state_identity',lambda:s.evidence_label(loss,bundle,lossrow['action']))
    x=deepcopy(g);x['after']['certificate']={'certified':True,'method':'recorded_terminal'}
    rejects('contradictory_positive_negative','contradictory',lambda:s.evidence_label(x,bundle,row['action']))
    x=deepcopy(row);x['diagnosis']='lost'
    rejects('changed_archived_label','archived_record_label',lambda:s.verify_grade_replay(bundle,x,computed['A1',2],g))
    x=deepcopy(g);x['after']['witness_result']['trajectory'][-1]['private_after'][0]+=0.001
    rejects('future_witness_value_corrupted','numeric',lambda:s.compare(actual['A1',2],x))
    x=deepcopy(saved);x['records'][0]=deepcopy(x['records'][1])
    rejects('duplicate_candidate_identity','unique_pool_index_identity',lambda:s.index_records(x,lock,grades))
    x=deepcopy(grades);x.pop(next(iter(x)))
    rejects('missing_grade_record','exact_grade_action_set',lambda:s.index_records(saved,lock,x))
    x=deepcopy(saved);x['selectors'][3]['diagnoses']['A1']='preserved'
    rejects('changed_crossed_label','selector:path_peak',lambda:s.select(data,x,computed))
    x=deepcopy(data);x['boundary01_history']['actions'][0][0]+=0.001
    rejects('plan_for_different_history','plan_history_identity',lambda:s.recompute_plans(x,bundle,rows))
    with tempfile.TemporaryDirectory(prefix='pilot-source-fault-') as tmp:
        root=Path(tmp);names=list(report['source_sha256'])+['artifact/source/pilot-sensitivity-bindings.json']
        for name in names:
            p=root/name;p.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(s.H.parent/name,p)
        p=root/'artifact/source/pilot-sensitivity-grades.json';p.write_bytes(p.read_bytes()+b' ')
        rejects('changed_original_grade_bytes','source_hash:artifact/source/pilot-sensitivity-grades.json',lambda:s.load_sources(root))
    s.need(not root.exists(),'temporary_source_cleanup')
    print(json.dumps({'passed':True,'valid_replay':{'plans':report['plans_recomputed'],'grades':report['grade_records_replayed'],
      'selectors':len(report['selectors_recomputed']),'verification_local_physics_transitions':report['verification_local_physics_transitions']},
      'rejected_corruptions':checks,'negative_control_count':len(checks),'temporary_files_removed':True,
      'new_scientific_samples':0,'new_model_calls':0,'participant_programs_executed':0},sort_keys=True))
if __name__=='__main__':main()
