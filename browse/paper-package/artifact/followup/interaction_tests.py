"""Corrupt copies to check semantic binding; never execute archived programs."""
from pathlib import Path
import json,shutil,tempfile,sys
sys.path.insert(0,str(Path(__file__).resolve().parent))
from interaction_check import check,BASE,digest
def load(p):return json.loads(p.read_text())
def put(p,x):p.write_text(json.dumps(x,ensure_ascii=False,indent=2)+'\n')
def tests():
    positive=check();rejected=[]
    cases=['missing_call','wrong_request','wrong_profile','wrong_condition','changed_analysis_code','changed_tool_result','changed_history','changed_final','technical_as_completed','collector_bytes','unlisted_file']
    for name in cases:
        with tempfile.TemporaryDirectory(prefix='ruu-reader-negative-') as tmp:
            base=Path(tmp)/'followup';shutil.copytree(BASE,base);root=base/'interactions';idx=load(root/'INDEX.json')
            entry=next(x for x in idx['trials'] if len(x['calls'])>1);call=entry['calls'][0]
            if name=='missing_call':entry['calls'].pop()
            elif name=='wrong_request':call['request_id']='t999-q1'
            elif name=='wrong_profile':
                call['intent']['value']['profile']['reasoning_effort']='low'
                call['intent']['value_canonical_sha256']=digest(call['intent']['value'])
            elif name=='wrong_condition':
                p=root/call['prompt']['path'];p.write_text(p.read_text().replace('"condition":','"wrong_condition":',1))
            elif name=='changed_analysis_code':
                p=root/call['analysis_request']['path'];j=load(p);j['code']+='\n# changed';put(p,j)
            elif name=='changed_tool_result':
                p=root/call['analysis_result']['path'];put(p,{'status':'ok','value':'changed'})
            elif name=='changed_history':
                p=root/entry['calls'][1]['prompt']['path'];p.write_text(p.read_text().replace('"analysis_records":','"analysis_records_changed":',1))
            elif name=='changed_final':
                p=root/entry['calls'][-1]['response']['path'];j=load(p);j['decision']['action_id']=999;put(p,j)
            elif name=='technical_as_completed':idx['trials'][12]['status']='completed'
            elif name=='collector_bytes':
                p=root/idx['collectors'][0]['path'];p.write_text(p.read_text()+'\n# changed\n')
            elif name=='unlisted_file':(root/'unexpected.txt').write_text('unexpected')
            put(root/'INDEX.json',idx)
            # Disable member hashes for semantic tests so rejection cannot rely only on hashes.
            try:check(base,verify_bytes=name=='collector_bytes')
            except (ValueError,KeyError,AssertionError,FileNotFoundError):rejected.append(name)
            else:raise AssertionError('corruption accepted: '+name)
    return {'passed':True,'positive_archived_dataset':positive,'negative_controls_rejected':rejected,'semantic_checks_not_just_hashes':10,'new_model_calls':0,'new_physics_runs':0}
if __name__=='__main__':print(json.dumps(tests(),sort_keys=True,indent=2))
