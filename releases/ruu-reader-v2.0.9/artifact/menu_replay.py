"""Recompute the 32 existing menu labels using the distributed numerical evaluator.
Continuous L remains conditional on the manuscript's numerical/runtime premises.
"""
from pathlib import Path
from collections import Counter,defaultdict
import sys,json,hashlib
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent/'legacy-replay/src'))
from transferreplay import grading

def read(p):return json.loads(p.read_bytes())
def digest(v):return hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':'),ensure_ascii=False).encode()).hexdigest()
def need(ok,code):
    if not ok:raise ValueError(code)
def main():
    d=read(H/'data/crossing.json');summary=read(H/'data/protocol-summary.json');base=H.parent/'legacy-replay/data/transfer';cases={c['case_id']:c for c in read(base/'CASES.private.json')};labels={};steps=0
    mapping={'feasibility_preserved_by_witness':'P','feasibility_lost_by_certificate':'L'}
    for entry in summary['selected_histories']:
        cid=entry['public_id'];case=cases[entry['case_id']];path=base/case['delivery_path'];packet=read(path)
        need(hashlib.sha256(path.read_bytes()).hexdigest()==case['delivery_sha256'],'packet_binding')
        public_path=H/'protocol/inputs'/(cid+'.json');public=read(public_path)
        need(hashlib.sha256(public_path.read_bytes()).hexdigest()==entry['source_packet_sha256'],'public_packet_binding')
        need(public['history']==packet['history'] and public['physical_step']==packet['physical_step'],'public_private_history')
        need(digest(packet['history'])==entry['history_sha256'],'history_binding')
        menu=d['contexts'][cid]['menu'];need(digest(menu)==entry['menu_sha256']==d['labelmaps'][cid]['menu_sha256'],'menu_binding')
        got=[]
        for action in menu:
            grade=grading.grade_case(case,packet,{'action':action});got.append(mapping.get(grade['diagnostic_score'],'U'));steps+=grade['local_physics_steps']
        need(got==d['labelmaps'][cid]['labels'],'recomputed_menu_labels:'+cid);labels[cid]=got
    counts=defaultdict(Counter)
    for a in d['allocation']:
        r=d['trials'][a['trial_id']]['result'];counts[a['condition']+'/'+a['family']][r['label']]+=1
    print(json.dumps({'passed':True,'menu_labels_recomputed':sum(map(len,labels.values())),'labels':labels,'native_labels_by_condition_family':dict(counts),'evaluator_counted_steps':steps,'new_live_samples':0,'model_calls':0,'participant_programs_executed':0,'continuous_labels_conditional':True,'independent_laboratory':False},sort_keys=True))
if __name__=='__main__':main()
