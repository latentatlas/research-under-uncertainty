"""Semantic corruption controls on disposable copies; no model or physics."""
from pathlib import Path
import json,hashlib,tempfile,shutil,subprocess,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
def read(p):return json.loads(p.read_text())
def write(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def rebind(d):
    p=d/'SOURCE-BINDINGS.json';v=read(p)
    for n in v['files']:v['files'][n]=sha(d/n)
    write(p,v)
def entry(d,segment,rid):
    index=read(d/'INDEX.json');s=next(s for s in index['segments'] if s['id']==segment)
    return index,s,next(r for r in s['roles'] if r['role_id']==rid)
def edit_response(d,rid,fn,segment='initial'):
    _,_,r=entry(d,segment,rid);q=d/r['requests'][-1]['path']/'response.json';v=read(q);fn(v['decision']);write(q,v)
def run(d):return subprocess.run([sys.executable,'-I','-B','-S',str(d/'check.py')],cwd=d,text=True,capture_output=True,timeout=30)
def test(d,name):
    if name=='action_outside_menu':edit_response(d,'r064',lambda x:x.update(action_id='not-in-menu'),'completion')
    elif name=='wrong_case_identity':edit_response(d,'r064',lambda x:x.update(case_id='wrong-case'),'completion')
    elif name=='source_numeric_range':edit_response(d,'r058',lambda x:x['record']['table']['candidate_losses'][0].__setitem__(0,1.1))
    elif name=='packet_menu_identity':
        p=d/'packets/h04.json';v=read(p);v['targets'][1]['menu_sha256']='0'*64;write(p,v)
    elif name in ('record_removed_from_R','record_added_to_NR'):
        rid='r062' if name=='record_removed_from_R' else 'r063';index,_,r=entry(d,'completion',rid);q=d/r['requests'][0]['path']/'prompt.txt'
        prefix,payload=q.read_text().split('\nPUBLIC INPUT\n',1);v=json.loads(payload);v['source_record_json']=None if rid=='r062' else '{}'
        from strict_io import canonical
        q.write_text(prefix+'\nPUBLIC INPUT\n'+canonical(v));r['requests'][0]['prompt_sha256']=sha(q);write(d/'INDEX.json',index)
    elif name=='missing_assigned_role':
        index,segment,_=entry(d,'initial','r064');segment['roles'].pop();write(d/'INDEX.json',index)
    elif name=='mock_presented_as_live':
        index,segment,_=entry(d,'completion','r064');segment['mock_only']=True;write(d/'INDEX.json',index)
    elif name=='profile_changed':
        index,_,r=entry(d,'completion','r062');r['requests'][0]['profile']['reasoning_effort']='low';write(d/'INDEX.json',index)
    elif name=='unresolved_usage_zeroed':
        index,_,r=entry(d,'initial','r062');r['requests'][0]['usage']={'input_tokens':0,'output_tokens':0};write(d/'INDEX.json',index)
    elif name in ('cache_double_count','reasoning_not_subset'):
        index,_,r=entry(d,'completion','r064');req=r['requests'][0];k='cached_input_tokens' if name=='cache_double_count' else 'reasoning_output_tokens';limit='input_tokens' if name=='cache_double_count' else 'output_tokens';req['usage'][k]=req['usage'][limit]+1
        p=d/req['path']/'usage-events.json';v=read(p);v[0]['usage'][k]=req['usage'][k];write(p,v);write(d/'INDEX.json',index)
    elif name=='prediction_lock_after_target':
        p=d/'segments/completion/events.json';v=read(p);target=next(x for x in v if x['kind']=='role_start' and x['role_id']=='r064');obs=next(x for x in v if x['kind']=='role_result' and x['role_id']=='r063');obs['utc']=target['utc'];write(p,v)
    elif name=='fabricated_source_structure':
        p=d/'REFERENCE.json';v=read(p);v['combined']['by_profile']['gpt-6.1-sol']['single_row_records']=4;write(p,v)
    elif name=='analysis_result_changed':
        q=next(d.glob('segments/initial/*/*/analysis.json'));v=read(q);v['result']={'fabricated':True};write(q,v)
    elif name=='target_changes_accuracy':
        index,_,r=entry(d,'completion','r062');pred=read(d/r['requests'][-1]['path']/'response.json')['decision']['action_id']
        edit_response(d,'r064',lambda x:x.update(action_id=pred),'completion')
    else:raise ValueError(name)
def main():
    baseline=run(H);assert baseline.returncode==0,baseline.stderr
    cases=['action_outside_menu','wrong_case_identity','source_numeric_range','packet_menu_identity','record_removed_from_R','record_added_to_NR','missing_assigned_role','mock_presented_as_live','profile_changed','unresolved_usage_zeroed','cache_double_count','reasoning_not_subset','prediction_lock_after_target','fabricated_source_structure','analysis_result_changed','target_changes_accuracy']
    results=[]
    with tempfile.TemporaryDirectory(prefix='ruu-prospective-negative-') as temp:
        root=Path(temp)
        for name in cases:
            d=root/name;shutil.copytree(H,d);test(d,name);rebind(d)
            r=run(d);assert r.returncode!=0,'Corruption escaped: '+name
            results.append({'case':name,'rejected':True,'reason':r.stderr.strip().splitlines()[-1]})
    print(json.dumps({'passed':True,'negative_control_count':len(results),'cases':results,'hashes_rebound_to_test_semantics':True,'temporary_files_removed':not root.exists(),'model_calls':0,'world_or_submitted_programs_executed':0},sort_keys=True))
if __name__=='__main__':main()
