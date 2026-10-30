"""Recompute choices, records, chronology and usage from visible evidence.

Standard library only. Never execute a submitted analysis or a world simulator.
The supplied sequence/receipt projections do not authenticate a remote provider.
"""
from pathlib import Path
import sys,json,hashlib,copy
from decimal import Decimal
from datetime import datetime
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
from common import read_json,sha,MODELS
from protocol import parse_response,payload_for,render,schema,get_bundle
from readout import summarize

def require(ok,code):
    if not ok:raise ValueError(code)

def cost(model,u):
    ri,rc,ro=map(Decimal,('250','25','1250') if model==MODELS[0] else ('50','2.5','250'))
    u={'input_tokens':1050000,'output_tokens':128000} if u is None else u
    i,o,c=u['input_tokens'],u['output_tokens'],u.get('cached_input_tokens',0)
    require(all(type(x) is int and x>=0 for x in (i,o,c)) and c<=i,'usage_range')
    return ((i-c)*ri+c*rc+o*ro)*2/Decimal(1000000)

def audit():
    bindings=read_json(H/'SOURCE-BINDINGS.json')
    for rel,h in bindings['files'].items():
        p=Path(rel);require(not p.is_absolute() and '..' not in p.parts,'unsafe_binding')
        require(not (H/rel).is_symlink() and sha(H/rel)==h,'source_hash:'+rel)
    index=read_json(H/'INDEX.json');rows=read_json(H/'ALLOCATION.json')['rows'];byid={r['role_id']:r for r in rows}
    require(len(rows)==64 and len(byid)==64,'allocation')
    require([s['id'] for s in index['segments']] in (['initial'],['initial','completion']),'segment_order')
    sources={};source_locks={};all_results={};reports={};usage={};request_total=0;analysis_count=0
    control_answers=read_json(H/'CONTROL-ANSWERS.json')['answers']
    for segment in index['segments']:
        label=segment['id']; entries=segment['roles'];events=read_json(H/f'segments/{label}/events.json')
        expected=list(byid) if label=='initial' else ['r005','r006','r007','r008','r062','r063','r064']
        require([r['role_id'] for r in entries]==expected,'segment_role_coverage')
        require(not segment['mock_only'],'mock_evidence')
        require(segment['allocation_sha256']==sha(H/'ALLOCATION.json'),'allocation_source_identity')
        require(segment['closure_present']==(label=='completion'),'segment_closure_claim')
        require([e['sequence'] for e in events]==list(range(1,len(events)+1)),'event_sequence')
        require(all(datetime.fromisoformat(events[i]['utc'])<=datetime.fromisoformat(events[i+1]['utc']) for i in range(len(events)-1)),'event_time_order')
        event_index={}
        for event in events:
            key=(event['kind'],event['role_id'],event['request_id'])
            if key[0] in ('role_start','role_result','request_intent','request_receipt'):
                require(key not in event_index,'duplicate_event');event_index[key]=event
        def ev(kind,rid,qid=None):return event_index.get((kind,rid,qid))
        results=[];committed={};request_rows=[];started_order=[]
        for ent in entries:
            rid=ent['role_id'];row=byid[rid];role=row['role'];source=sources.get(row['unit_id']);calls=ent['requests']
            start=ev('role_start',rid);finish=ev('role_result',rid)
            require(ent['started']==(start is not None),'role_started_evidence')
            if start:started_order.append(rid)
            if role in ('observer','target') and start:
                require(source is not None and source['status']=='completed','missing_source')
                require(source_locks[row['unit_id']]<datetime.fromisoformat(start['utc']),'source_after_target')
                controls=[x for x in results if x['role']=='control']
                required=8 if label=='initial' else 4
                require(len(controls)==required and all(x['status']=='completed' for x in controls),'control_gate_protocol')
                for c in controls:
                    cr=byid[c['role_id']]
                    if cr['condition']=='with_record':require(c['action_id']==control_answers[cr['case_id']],'control_gate_accuracy')
            if role=='target' and start:
                obs=[r['role_id'] for r in rows if r['role']=='observer' and r['unit_id']==row['unit_id'] and r['target_index']==row['target_index']]
                require(all(o in committed and committed[o]<datetime.fromisoformat(start['utc']) for o in obs),'target_before_prediction_lock')
            require(len(calls)<=row['max_requests'],'request_limit')
            analyses=[];final=None;any_fault=False;protocol_fault=False
            for qi,req in enumerate(calls,1):
                require(req['q']==qi and req['request_id']==rid+f'-q{qi}','request_identity')
                require(req['path']==f'segments/{label}/{rid}/q{qi}','request_path')
                require(not req['mock_only'] and req['profile']==row['profile'] and req['profile_sha256']==row['profile_sha256'],'profile_identity')
                require(0<req['timeout_seconds']<=900,'request_allowance')
                q=H/req['path'];intent=ev('request_intent',rid,req['request_id']);receipt=ev('request_receipt',rid,req['request_id'])
                require(intent is not None and start and intent['sequence']>start['sequence'],'request_before_role')
                require(req['receipted']==(receipt is not None),'receipt_presence')
                if receipt:require(receipt['sequence']>intent['sequence'],'receipt_before_intent')
                require(sha(q/'prompt.txt')==req['prompt_sha256'] and sha(q/'schema.json')==req['schema_sha256'],'input_binding')
                require((q/'prompt.txt').read_text()==render(row,payload_for(row,source,analyses)),'role_information_boundary')
                require(read_json(q/'schema.json')==schema(role),'schema_boundary')
                telemetry=read_json(q/'usage-events.json');u=None
                if req['receipted'] and req['usage'] is not None:
                    require(len(telemetry)==1,'usage_event_count')
                    u=dict(telemetry[0]['usage']);measured='cached_input_tokens' in u
                    require(measured==req['cached_input_measured'],'cache_split_claim')
                    u.setdefault('cached_input_tokens',0)
                    require(u==req['usage'],'usage_event_mismatch')
                    require(u.get('reasoning_output_tokens',0)<=u['output_tokens'],'reasoning_subset')
                else:require(req['usage'] is None,'unreceipted_usage_fabricated')
                request_rows.append({'role':role,'model':row['model'],'usage':u,'cached_measured':req['cached_input_measured']})
                request_total+=1
                if req['receipted']:
                    any_fault |= bool(req['technical_faults']);protocol_fault |= bool(req['protocol_error'])
                    if not req['technical_faults'] and not req['protocol_error']:
                        envelope=parse_response((q/'response.json').read_text(),row)
                        if envelope['kind']=='final':
                            require(qi==len(calls),'request_after_final');final={k:v for k,v in envelope.items() if k!='kind'}
                        else:
                            ar=read_json(q/'analysis.json')
                            require(ar['code']==envelope['code'] and qi<=3,'analysis_binding')
                            analyses.append(ar);analysis_count+=1
                else:require(qi==len(calls),'request_after_unresolved')
            status=ent['status']
            if status=='completed':require(final is not None and not any_fault and not protocol_fault and finish is not None,'completed_without_valid_final')
            elif status=='protocol':require(protocol_fault and finish is not None,'unsubstantiated_protocol')
            elif status in ('interrupted','technical_interrupted'):require(start is not None and any(not q['receipted'] for q in calls),'unsubstantiated_interruption')
            elif status=='not_started':require(not calls and start is None,'unstarted_has_activity')
            elif status=='technical':require(any_fault,'unsubstantiated_technical')
            else:raise ValueError('unexpected_status')
            result=dict(final or {},role_id=rid,case_id=row['case_id'],model=row['model'],role=role,unit_id=row['unit_id'],status=status,started=ent['started'],requests=len(calls))
            if finish:
                require(start is not None or status=='not_started','finish_without_start')
                if calls:
                    last=ev('request_receipt',rid,calls[-1]['request_id'])
                    if last:require(finish['sequence']>last['sequence'],'finish_before_last_receipt')
                committed[rid]=datetime.fromisoformat(finish['utc'])
            if role=='source' and status=='completed':sources[row['unit_id']]=result;source_locks[row['unit_id']]=committed[rid]
            results.append(result)
        require(started_order==expected[:len(started_order)],'started_role_order')
        all_results[label]=results
        usage[label]={}
        for model in MODELS:
            rr=[r for r in request_rows if r['model']==model];known=[r for r in rr if r['usage'] is not None];un=len(rr)-len(known)
            usage[label][model]={'requests':len(rr),'measured_requests':len(known),'unknown_requests':un,
                'input_tokens':sum(r['usage']['input_tokens'] for r in known),'output_tokens':sum(r['usage']['output_tokens'] for r in known),
                'cached_input_tokens_subset':sum(r['usage']['cached_input_tokens'] for r in known if r['cached_measured']),
                'cache_split_unknown_measured_requests':sum(not r['cached_measured'] for r in known),
                'measured_credit_equivalent':str(sum((cost(model,r['usage']) for r in known),Decimal(0))),
                'unknown_credit_reserve':str(un*cost(model,None)),'unknown_reserved_input':un*1050000,'unknown_reserved_output':un*128000}
    reports['initial']=summarize(rows,all_results['initial'])
    reference=read_json(H/'REFERENCE.json')
    require(reports['initial']==reference['initial'],'initial_readout_mismatch')
    if 'completion' in all_results:
        completion={r['role_id']:r for r in all_results['completion']}
        rr=[completion[r['role_id']] if r['role_id'] in ('r062','r063','r064') else r for r in all_results['initial']]
        reports['combined']=summarize(rows,rr);require(reports['combined']==reference['combined'],'combined_readout_mismatch')
    require(reference['completion_included']==('completion' in all_results),'completion_presence')
    require(usage['initial'][MODELS[1]]['unknown_requests']==1 and Decimal(usage['initial'][MODELS[1]]['unknown_credit_reserve'])==169,'lost_original_unknown_reserve')
    controls={}
    for label,rr in all_results.items():
        controls[label]={}
        for model in MODELS:
            controls[label][model]={}
            for arm in ('with_record','without_record'):
                rs=[r for r in rr if r['role']=='control' and r['model']==model and byid[r['role_id']]['condition']==arm]
                controls[label][model][arm]={'correct':sum(r['status']=='completed' and r.get('action_id')==control_answers[r['case_id']] for r in rs),'valid':sum(r['status']=='completed' for r in rs),'assigned':len(rs)}
    return {'passed':True,'reports':reports,'usage':usage,'controls':controls,'visible_requests':request_total,'readable_analysis_pairs':analysis_count,
        'numeric_source_records_reparsed':8,'original_role_denominator':64,'completed_original_roles':sum(r['status']=='completed' for r in all_results['initial']),
        'completed_completion_roles':sum(r['status']=='completed' for r in all_results.get('completion',[])),
        'world_or_submitted_programs_executed':0,'model_calls':0,'original_unresolved_attempt_preserved':True,
        'independent_provider_attestation':False,'independent_replication':False,'world_prediction_accuracy_measured':False,
        'source_protocol_and_scalar_calculation_shared_with_collector':True}

if __name__=='__main__':print(json.dumps(audit(),sort_keys=True))
