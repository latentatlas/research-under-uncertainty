"""Common wire scaffold; final numeric tokens reach the frozen selector verbatim."""
from copy import deepcopy
import json
from pathlib import Path
from strict_io import canonical, digest, read_json
from executable_selector import MAX_BYTES

HERE = Path(__file__).resolve().parent
VERSION = 'executable-decision-wire-v1'
PROTOCOL = (HERE/'COMMON.txt').read_text()

def obj(properties):
    return {'type':'object','properties':properties,'required':list(properties),'additionalProperties':False}

RECORD = obj({k:{'type':'string'} for k in ('schema','case_id','menu_sha256','loss_definition_id','rule')} |
             {'candidate_losses':{'type':'array','items':{'type':'array','items':{'type':'number'}}}})
ANALYZE = obj({'analyze':{'type':'string'}})
# Identical in both arms: the schema does NOT enforce condition, menu identity,
# dimensions, numeric range, rule choice, or record-to-action agreement.
WIRE_SCHEMA = obj({'decision':{'anyOf':[ANALYZE, obj({'action_id':{'type':'integer'}}),
    obj({'record':RECORD}), obj({'action_id':{'type':'integer'},'record':RECORD})]}})

class ParticipantProtocolError(ValueError):
    def __init__(self, message, *, evidence_ref=None):
        super().__init__(message)
        self.kind='participant_protocol_error'; self.evidence_ref=evidence_ref

def _pairs(items):
    result={}
    for k,v in items:
        if k in result: raise ValueError('duplicate JSON key')
        result[k]=v
    return result

def _constant(value):
    raise ValueError('nonfinite JSON constant')

class NumericToken(str):
    """Keep numeric lexemes distinct from genuine JSON strings."""
DECODER=json.JSONDecoder(object_pairs_hook=_pairs,parse_int=NumericToken,parse_float=NumericToken,parse_constant=_constant)

def field_text(text, field):
    """Locate a value's original substring; never float-roundtrip a decision."""
    try:
        value=DECODER.decode(text)
        if type(value) is not dict or field not in value: raise ValueError('missing object field')
        i=text.index('{')+1
        while True:
            while text[i].isspace(): i+=1
            key,end=DECODER.raw_decode(text,i);i=end
            while text[i].isspace(): i+=1
            if text[i]!=':': raise ValueError('colon')
            i+=1
            while text[i].isspace(): i+=1
            start=i;_,i=DECODER.raw_decode(text,i)
            if key==field:return text[start:i]
            while text[i].isspace(): i+=1
            if text[i]!=',': raise ValueError('field not found')
            i+=1
    except (ValueError,IndexError,RecursionError,UnicodeError) as exc:
        raise ParticipantProtocolError('invalid JSON object: '+str(exc)) from exc

def parse_response(text):
    try:
        if type(text) is not str or len(text.encode())>1048576: raise ValueError('wire size')
        v=DECODER.decode(text)
        if type(v) is not dict or set(v)!={'decision'} or type(v['decision']) is not dict:
            raise ValueError('one decision object required')
        d=v['decision']
        if 'analyze' in d:
            if set(d)!={'analyze'} or type(d['analyze']) is not str or not 1<=len(d['analyze'])<=60000:
                raise ValueError('analysis shape/length')
            return {'decision':deepcopy(d)}
        return {'decision':{'final_text':field_text(text,'decision')}}
    except (ValueError,RecursionError,UnicodeError) as exc:
        raise ParticipantProtocolError(str(exc)) from exc

def validate_payload(p):
    fields={'snapshot','condition','analysis_records','remaining_analysis_calls','remaining_model_decisions'}
    if type(p) is not dict or set(p)!=fields:raise ValueError('public payload allowlist')
    s=p['snapshot'];cid=s.get('case_id') if type(s) is dict else None
    if cid not in ('probe-01','probe-02','probe-03','probe-04'):raise ValueError('opaque case')
    if s!=read_json(HERE/'inputs'/f'{cid}.json'):raise ValueError('exact public input identity')
    if digest(s['task']['action_menu'])!=s['menu_sha256']:raise ValueError('menu binding')
    if p['condition'] not in ('optional_record','executable_record'):raise ValueError('condition')
    rows=p['analysis_records']
    if type(rows) is not list or len(rows)>3:raise ValueError('analysis count')
    if p['remaining_analysis_calls']!=3-len(rows) or p['remaining_model_decisions']!=4-len(rows):raise ValueError('allowance')
    for r in rows:
        if type(r) is not dict or set(r)!={'submitted_code','result'} or type(r['submitted_code']) is not str or type(r['result']) is not dict:
            raise ValueError('analysis output allowlist')
    canonical(p)
    return True

def render(payload,protocol=PROTOCOL):
    validate_payload(payload)
    return protocol+'\n'+(HERE/(payload['condition']+'.txt')).read_text()+'\nVISIBLE RECORD\n'+canonical(payload)
