"""Participant allowlists, exact source record parsing and role identities."""
from copy import deepcopy
import json
import math
from fractions import Fraction
from common import HERE, MODELS, canonical, digest, read_json, loads, profile
from executable_selector import parse as exact_parse, _selection

def obj(p):
    return {'type':'object','properties':p,'required':list(p),'additionalProperties':False}

STR={'type':'string'}
TABLE=obj({k:STR for k in ('schema','case_id','menu_sha256','loss_definition_id','rule')} |
          {'candidate_losses':{'type':'array','items':{'type':'array','items':{'type':'number'}}}})
RECORD=obj({'table':TABLE, **{k:STR for k in ('assumptions','uncertainty','decision_criterion','expected_observation')}})
ACTION=obj({'case_id':STR,'action_id':STR})
SOURCE=obj({'case_id':STR,'action_id':STR,'record':RECORD})
ANALYZE=obj({'analyze':STR})

def schema(role):
    return obj({'decision':{'anyOf':[ANALYZE,SOURCE if role=='source' else ACTION]}}) if role in ('source','target') else obj({'decision':ACTION})

def field_text(text, field):
    # The entire document is separately strict-parsed; slicing avoids numeric float roundtrips.
    decoder=json.JSONDecoder();i=text.index('{')+1
    while True:
        while text[i].isspace():i+=1
        key,i=decoder.raw_decode(text,i)
        while text[i].isspace():i+=1
        if text[i]!=':':raise ValueError('field colon')
        i+=1
        while text[i].isspace():i+=1
        start=i;_,i=decoder.raw_decode(text,i)
        if key==field:return text[start:i]
        while text[i].isspace():i+=1
        if text[i]!=',':raise ValueError('field absent')
        i+=1

def validate_packet(p):
    fields={'case_id','family','history','physical_step','remaining_physical_steps','task','action_menu','action_ids','menu_sha256','history_sha256'}
    if set(p)!=fields or p['family'] not in ('continuous','route'):raise ValueError('packet allowlist')
    h=p['history'];s=p['physical_step'];n=p['task']['physical_horizon']
    if set(h)!={'states','actions'} or type(s) is not int or not 0<=s<n or len(h['states'])!=s+1 or len(h['actions'])!=s or p['remaining_physical_steps']!=n-s:
        raise ValueError('packet time/history')
    for a in h['states']+h['actions']+p['action_menu']:
        if type(a) is not list or len(a)!=2 or any(type(v) not in (int,float) or not math.isfinite(v) for v in a):raise ValueError('finite pair')
    ids=[digest({'family':p['family'],'action':a}) for a in p['action_menu']]
    if p['action_ids']!=ids or len(set(ids))!=len(ids) or p['menu_sha256']!=digest(p['action_menu']) or p['history_sha256']!=digest(h):raise ValueError('packet/action identity')
    if p['family']=='continuous':
        if any(math.hypot(*a)>.600000001 for a in h['actions']+p['action_menu']) or any(math.hypot(*z)>4 for z in h['states']):raise ValueError('continuous legality')
    else:
        if any(a not in [[0,0],[1,0],[2,0]] for a in h['actions']+p['action_menu']):raise ValueError('route action')
        if any(f<0 or x>=18 for x,f in h['states']):raise ValueError('closed route')
    return True

def get_bundle(history_id):
    if history_id not in ('h01','h02','h03','h04'):raise ValueError('unknown history')
    b=read_json(HERE/'packets'/f'{history_id}.json')
    if b['history_id']!=history_id:raise ValueError('history binding')
    for p in [b['source']]+b['targets']:validate_packet(p)
    return b

def validate_row(row):
    registered=read_json(HERE/'ALLOCATION.json')['rows']
    if row not in registered:raise ValueError('unknown or changed allocation')
    if row['profile']!=profile(row['model']):raise ValueError('profile drift')
    if row['profile_sha256']!=digest(row['profile']):raise ValueError('profile identity')

def payload_for(row, source=None, analysis_records=None):
    validate_row(row)
    role=row['role']; analyses=deepcopy(analysis_records or [])
    if role=='control':
        controls=read_json(HERE/'CONTROL-PUBLIC.json')['cases']
        c=deepcopy(controls[row['control_case']])
        if row['condition']=='without_record':c['source_record']=None
        return {'role':'observer_control','case_id':row['case_id'],'public_evidence':c,'condition':row['condition']}
    b=get_bundle(row['history_id']);s=b['source']
    if role=='source':
        if source is not None:raise ValueError('source cannot receive its own result')
        return {'role':'source','snapshot':s,'analysis_records':analyses,'remaining_analyses':3-len(analyses)}
    if type(source) is not dict or source.get('status')!='completed' or source.get('case_id')!=s['case_id'] or source.get('action_id') not in s['action_ids']:
        raise ValueError('source result dependency')
    t=b['targets'][row['target_index']]
    if row['case_id']!=t['case_id']:raise ValueError('target identity')
    evidence={'source_snapshot':s,'source_action_id':source['action_id'],'target_snapshot':t,
        'target_origin':'precommitted independent branch from source history, not necessarily the source-proposed action'}
    if role=='target':
        return {'role':'target','public_evidence':evidence,'analysis_records':analyses,'remaining_analyses':3-len(analyses)}
    if analyses:raise ValueError('observer has no analysis tool')
    return {'role':'observer','public_evidence':evidence,'condition':row['condition'],
            'public_actor_contracts':{name:{'instructions':(HERE/'prompts'/f'{name}.txt').read_text(),'output_schema':schema(name)} for name in ('source','target')},
            'source_record_json':source['record_raw'] if row['condition']=='with_record' else None}

def render(row, payload):
    role=row['role'];name='observer' if role in ('observer','control') else role
    return (HERE/'prompts'/f'{name}.txt').read_text()+'\nPUBLIC INPUT\n'+canonical(payload)

def parse_response(raw, row):
    if not isinstance(raw,str) or len(raw.encode())>1048576:raise ValueError('response size')
    v=loads(raw)
    if type(v) is not dict or set(v)!={'decision'} or type(v['decision']) is not dict:raise ValueError('decision envelope')
    d=v['decision']; role=row['role']
    if 'analyze' in d:
        if role not in ('source','target') or set(d)!={'analyze'} or type(d['analyze']) is not str or not 1<=len(d['analyze'])<=60000:raise ValueError('analysis envelope')
        return {'kind':'analyze','code':d['analyze']}
    expected={'case_id','action_id','record'} if role=='source' else {'case_id','action_id'}
    if set(d)!=expected or d['case_id']!=row['case_id'] or type(d['action_id']) is not str:raise ValueError('final identity/fields')
    if role=='control':
        menu=read_json(HERE/'CONTROL-PUBLIC.json')['cases'][row['control_case']]['target']['action_ids']
    else:
        b=get_bundle(row['history_id']);p=b['source'] if role=='source' else b['targets'][row['target_index']];menu=p['action_ids']
    if d['action_id'] not in menu:raise ValueError('action not in bound menu')
    result={'kind':'final','case_id':d['case_id'],'action_id':d['action_id']}
    if role=='source':
        record=d['record']
        fields={'table','assumptions','uncertainty','decision_criterion','expected_observation'}
        if type(record) is not dict or set(record)!=fields:raise ValueError('record fields')
        for k in fields-{'table'}:
            if type(record[k]) is not str or len(record[k])>6000:raise ValueError('record text type/length')
        raw_record=field_text(field_text(raw,'decision'),'record')
        raw_table=field_text(raw_record,'table')
        selection=_selection(exact_parse(raw_table),{'case_id':p['case_id'],'menu':p['action_menu'],'menu_sha256':p['menu_sha256']})
        result.update(record_raw=raw_record,record_sha256=__import__('hashlib').sha256(raw_record.encode()).hexdigest(),
            record_diagnostics=selection['diagnostics'],record_selected_action_id=p['action_ids'][selection['action_id']],
            record_proposal_agree=p['action_ids'][selection['action_id']]==d['action_id'])
    return result

def action_copy(source, target):
    return source['action_id'] if source['action_id'] in target['action_ids'] else None
