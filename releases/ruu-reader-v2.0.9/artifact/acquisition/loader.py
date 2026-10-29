"""Decode the original committed records and verify original-byte identities."""
from pathlib import Path
import json,hashlib
from codec import unpack,original_bytes
H=Path(__file__).resolve().parent

def need(ok,code):
    if not ok:raise ValueError(code)
def read(p):return json.loads(p.read_bytes())
def digest_bytes(data):return hashlib.sha256(data).hexdigest()
def canonical(v):return json.dumps(v,sort_keys=True,separators=(',',':'),allow_nan=False).encode()
def source(name):
    rel='source/'+name+'.json';b=read(H/'SOURCE-BINDINGS.json')['files'][rel];raw=(H/rel).read_bytes()
    need(digest_bytes(raw)==b['distributed_sha256'],'distributed_source:'+name)
    v=json.loads(raw)
    if b.get('storage')=='lossless_columns':v=unpack(v['column_schema'],v['rows'])
    need(digest_bytes(original_bytes(v,b['original_encoding']))==b['source_sha256'],'original_source:'+name)
    return v

def original_hash(name):return read(H/'SOURCE-BINDINGS.json')['files']['source/'+name+'.json']['source_sha256']
def records():
    rows=[r for p in sorted(H.glob('records-??.json')) for r in read(p)]
    result=unpack(read(H/'record-schema.json'),rows);c=source('commitment');plan=source('record-plan')
    need(len(result)==c['planned_N']==plan['planned_N']==5000,'N')
    need(c['plan_sha256']==original_hash('record-plan') and c['truth_reads_before_commitment']==0,'commit_plan')
    need(plan['planned_ids']==[f't{i:04d}' for i in range(1,5001)],'planned_order')
    for r,(tid,h) in zip(result,c['ordered_rows']):
        need(tid==r['view']['trial_id'],'record_identity')
        need(digest_bytes(canonical(r)+b'\n')==h,'original_record_bytes:'+tid)
        need(digest_bytes(canonical(r['view']))==plan['views'][tid],'view_identity:'+tid)
        need(r['original_unchanged'],'original_mutation')
        for arm,a in r['arms'].items():
            need(a['process']['exited'] and a['process']['exit_code']==0 and not a['process']['forced_cleanup'],'historical_exit_record')
            need(a['process']['pid']==a['result']['pid'],'pid_binding')
            for key,field in [('selection','selection_sha256'),('observation','observation_sha256')]:
                need(digest_bytes(canonical(a[key]))==a['result'][field],'arm_hash_chain')
    events=source('events')
    need([e['event'] for e in events]==['pair_committed']*5000+['all_pairs_sealed']+['truth_read']*5000,'commit_before_truth')
    return result

def project_records(raw=None,truth=None):
    raw=records() if raw is None else raw;truth=source('truth-audit') if truth is None else truth
    need([r['view']['trial_id'] for r in raw]==[x['trial_id'] for x in truth],'truth_order')
    out=[]
    fields=('trial_id','arm','certificate','compatible_before','compatible_after','initial_target_cardinality','output','prediction','query_id','target_values','timing','work')
    for r,t in zip(raw,truth):
        arms={}
        for name,a in r['arms'].items():
            arms[name]={k:a['result'][k] for k in fields}
            arms[name].update(exited=a['process']['exited'],possible_gain_loss=a['selection']['possible_gain_loss'],pre_observation_query_evaluations=a['selection']['pre_observation_query_evaluations'])
        out.append({'trial_id':r['view']['trial_id'],'truth':t['truth'],'arms':arms,'environment_work':r['environment_work']})
    return out
