"""Read archived visible interactions as data. No participant/collector code execution."""
from pathlib import Path
import hashlib,json
BASE=Path(__file__).resolve().parent
def read(p):return json.loads(p.read_text())
def canonical(x):return json.dumps(x,sort_keys=True,separators=(',',':'),ensure_ascii=False,allow_nan=False)
def digest(x):return hashlib.sha256(canonical(x).encode()).hexdigest()
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def require(condition,reason):
    if not condition:raise ValueError(reason)
def check(base=BASE,verify_bytes=True):
    base=Path(base);root=base/'interactions';index=read(root/'INDEX.json')
    require(index['schema']=='ruu-visible-interactions-v1','schema')
    rows=read(base/'allocation.json')['rows'];trials=read(base/'trials.json')['trials']
    finals={x['order']:x for x in read(base/'final-index.json')['entries']}
    require([x['order'] for x in rows]==list(range(1,49)),'allocation order')
    require([x['order'] for x in index['trials']]==list(range(1,49)),'interaction order')
    seen={'INDEX.json'}
    def member(binding):
        rel=binding['path'];p=root/rel
        require(not Path(rel).is_absolute() and '..' not in Path(rel).parts,'unsafe path')
        require(p.is_file() and not p.is_symlink(),'missing member')
        require(rel not in seen,'duplicate member');seen.add(rel)
        if verify_bytes:require(sha(p)==binding['sha256'],'member hash')
        if binding['mode']=='exact_bytes':require(binding['source_sha256']==binding['sha256'],'exact source hash')
        return p
    def projected(binding):
        if binding.get('mode')=='inline_projection':
            require(digest(binding['value'])==binding['value_canonical_sha256'],'inline projection hash')
            return binding['value']
        return read(member(binding))
    packets={case:read(member(binding)) for case,binding in index['packets'].items()}
    totals={'requests':0,'responses':0,'analyses':0,'completed':0,'technical':0};profiles={};visible_messages=0
    for row,trial,entry in zip(rows,trials,index['trials'],strict=True):
        order=row['order'];segment=1 if order<=13 else 2 if order==14 else 3
        require(trial['allocation']==row and entry['trial_id']==row['trial_id'],'trial identity')
        require(entry['segment']==segment==trial['segment'],'segment identity')
        require(entry['status']==trial['status'],'trial status')
        require(row['profile_sha256']==digest(row['profile']),'profile digest')
        packet=packets[row['case_id']]
        require(digest(packet)==row['packet_sha256'],'packet identity')
        require(digest(packet['task']['action_menu'])==row['menu_sha256']==packet['menu_sha256'],'menu identity')
        pc=profiles.setdefault(row['model'],{k:0 for k in totals});history=[];final_count=0;fault_count=0
        calls=entry['calls'];require(1<=len(calls)<=4 and len(calls)==trial['model_requests'],'call count')
        for q,call in enumerate(calls,1):
            request_id=f't{order:03d}-q{q}'
            require(call['request_id']==request_id,'request sequence')
            prompt=member(call['prompt']);intent=projected(call['intent']);receipt=read(member(call['receipt']))
            require(set(intent)==set(call['intent']['fields']) and set(receipt)==set(call['receipt']['fields']),'projection fields')
            require(intent['request_id']==receipt['request_id']==request_id,'request identity')
            require(intent['trial_id']==receipt['trial_id']==row['trial_id'],'receipt trial identity')
            require(intent['profile']==row['profile'] and intent['profile_sha256']==receipt['profile_sha256']==row['profile_sha256'],'profile binding')
            require(intent['mock_only'] is False and receipt['mock_only'] is False,'live status')
            require(intent['timeout_seconds']==900,'request timeout')
            require(intent['schema_sha256']==sha(base/'protocol/wire-schema.json'),'schema binding')
            require(receipt['intent_sha256']==call['intent']['source_sha256'],'source intent binding')
            if verify_bytes:require(sha(prompt)==intent['prompt_sha256'],'intent prompt hash')
            expected_payload={'snapshot':packet,'condition':row['arm'],'analysis_records':history,
                'remaining_analysis_calls':3-len(history),'remaining_model_decisions':4-len(history)}
            expected=(base/'protocol/COMMON.txt').read_text()+'\n'+(base/'protocol'/(row['arm']+'.txt')).read_text()+'\nVISIBLE RECORD\n'+canonical(expected_payload)
            require(prompt.read_text()==expected,'prompt cumulative history or condition mismatch')
            messages=read(member(call['messages']))
            require(messages['request_id']==request_id,'visible message identity')
            require(len(messages['messages'])==receipt['agent_message_count'],'visible message count')
            require(messages['used_response_message']==(len(messages['messages'])-1 if messages['messages'] else None),'selected visible message')
            visible_messages+=len(messages['messages'])
            for c in (totals,pc):c['requests']+=1
            if 'response' not in call:
                require(order in (13,14) and q==len(calls) and receipt['technical_faults'],'technical loss identity')
                require(receipt['agent_message_count']==0 and receipt['usage'] is None,'unknown usage preserved')
                require(not any(k in call for k in ('analysis_request','analysis_result','analysis_receipt')),'technical analysis')
                fault_count+=1;continue
            response_path=member(call['response']);envelope=read(response_path)
            require(set(envelope)=={'decision'},'response envelope');response=envelope['decision']
            require(not receipt['technical_faults'] and receipt['protocol_error'] is None,'response fault')
            require(receipt['agent_message_count']>=1 and receipt['usage'] is not None,'response receipt')
            require(response_path.read_text() in (messages['messages'][-1],messages['messages'][-1]+'\n'),'selected response binding')
            for c in (totals,pc):c['responses']+=1
            if 'analyze' in response:
                require(set(response)=={'analyze'} and isinstance(response['analyze'],str),'analysis envelope')
                require(q<len(calls),'analysis without next request')
                request=read(member(call['analysis_request']));result=read(member(call['analysis_result']));ar=projected(call['analysis_receipt'])
                require(request=={'code':response['analyze'],'history':packet['history']},'analysis input binding')
                require(ar['infrastructure_failure'] is False and ar['participant_resource_stop'] is False,'analysis receipt status')
                require(ar['result_canonical_sha256']==digest(result) and result['status']=='ok','analysis result binding')
                require(set(result)=={'status','value'},'analysis result allowlist')
                history.append({'submitted_code':response['analyze'],'result':result})
                for c in (totals,pc):c['analyses']+=1
            else:
                require(q==len(calls) and order in finals,'final position')
                require(response_path.read_bytes()==(base/finals[order]['file']).read_bytes(),'final source binding')
                require(not any(k in call for k in ('analysis_request','analysis_result','analysis_receipt')),'final analysis')
                final_count+=1
        require(len(history)==trial['analyses'] and trial['analysis_errors']==0,'analysis count')
        require((final_count,fault_count)==((1,0) if trial['status']=='completed' else (0,1)),'terminal status')
        for c in (totals,pc):c[trial['status']]+=1
    for collector in index['collectors']:
        p=member(collector);require(str(p).endswith('.py.txt'),'collector must be inspection-only text')
    actual={str(p.relative_to(root)) for p in root.rglob('*') if p.is_file()}
    require(actual==seen,'unlisted or missing interaction member')
    require(not any(p.is_symlink() for p in root.rglob('*')),'symlink')
    require(totals==index['counts']=={'requests':120,'responses':118,'analyses':72,'completed':46,'technical':2},'aggregate reconciliation')
    require({k:v['analyses'] for k,v in profiles.items()}=={'gpt-6-astra':36,'gpt-6.1-sol':36},'analysis profile reconciliation')
    require(visible_messages==index['visible_agent_messages']==177,'visible message total')
    return {'passed':True,'counts':totals,'by_profile':profiles,'collector_sources_inspected_as_data':len(index['collectors']),
            'cumulative_prompt_reconstruction':True,'visible_agent_messages':visible_messages,'finals_bound_to_existing_tables':46,
            'participant_programs_executed':0,'new_model_calls':0,'new_physics_runs':0,
            'scope':'Archived application-visible prompts/responses/tool results; source receipt projections are not independent historical or provider attestation. Hidden reasoning and provider-added context are outside scope.'}
if __name__=='__main__':print(json.dumps(check(),sort_keys=True,indent=2))
