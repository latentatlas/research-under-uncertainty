"""Render and identity-check all 80 archived requests; never execute analysis text."""
from pathlib import Path
import json,hashlib,sys,argparse
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parent))
import wire

def sha(b):return hashlib.sha256(b).hexdigest()
def read(p):return json.loads(p.read_bytes())
def need(ok,code):
    if not ok:raise ValueError(code)
def render(row):
    p=row['payload'];condition=p['condition'];need(condition in ('optional_record','executable_record'),'condition')
    return (H/'COMMON.txt').read_text()+'\n'+(H/(condition+'.txt')).read_text()+'\nVISIBLE RECORD\n'+json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)
def check():
    for n,b in read(H/'SOURCE-BINDINGS.json')['files'].items():need(sha((H/n).read_bytes())==b['distributed_sha256'],'protocol_source:'+n)
    rows=[r for p in sorted(H.glob('requests-??.json')) for r in read(p)]
    need([r['call'] for r in rows]==list(range(1,81)),'ordered_80_requests')
    cross=read(H.parent/'data/crossing.json');alloc={a['trial_id']:a for a in cross['allocation']};counts={t:0 for t in alloc}
    for row in rows:
        a=alloc[row['trial_id']];p=row['payload'];counts[row['trial_id']]+=1
        need(row['decision']==counts[row['trial_id']] and row['profile']==a['profile'],'request_trial_profile')
        need(p['condition']==a['condition'] and p['snapshot']==read(H/'inputs'/(a['case_id']+'.json')),'payload_snapshot')
        need(row['call'] in cross['trials'][row['trial_id']]['result']['calls'],'request_binding')
        need(sha(render(row).encode())==row['prompt_sha256'],'exact_prompt')
        enc=(json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':'),allow_nan=False)+'\n').encode()
        need(sha(enc)==row['payload_file_sha256'],'exact_payload_bytes')
    for t,n in counts.items():need(n==len(cross['trials'][t]['result']['calls']),'trial_call_count')
    need(read(H/'wire-schema.json')==wire.WIRE_SCHEMA,'wire_schema')
    return {'passed':True,'requests':80,'trials':32,'exact_prompt_hashes':80,'exact_payload_hashes':80,'profile_scope':'Configured labels, not independent provider identity attestation','model_calls':0,'participant_programs_executed':0}
if __name__=='__main__':
    p=argparse.ArgumentParser(description=__doc__);p.add_argument('--show-call',type=int);a=p.parse_args();result=check()
    if a.show_call:
        rows=[r for f in sorted(H.glob('requests-??.json')) for r in read(f)];found=[r for r in rows if r['call']==a.show_call];need(len(found)==1,'call_id');print(render(found[0]))
    else:print(json.dumps(result,sort_keys=True))
