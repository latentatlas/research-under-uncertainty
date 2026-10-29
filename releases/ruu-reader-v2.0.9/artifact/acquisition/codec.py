"""Transparent, lossless columnar JSON. No compression, executable payload or IO side effects."""
import json

def flatten(value,path=()):
    if isinstance(value,dict):
        out={}
        for key,child in sorted(value.items()):out.update(flatten(child,path+(key,)))
        return out
    return {path:value}

def pack(rows):
    flat=[flatten(x) for x in rows]
    keys=sorted(flat[0])
    if not all(sorted(x)==keys for x in flat):raise ValueError('columnar field sets differ')
    constants={k:flat[0][k] for k in keys if all(x[k]==flat[0][k] for x in flat)}
    variables=[k for k in keys if k not in constants]
    return {'schema':'lossless-json-columns-v1','N':len(rows),
            'constants':[[list(k),v] for k,v in constants.items()],
            'columns':[list(k) for k in variables]},[[r[k] for k in variables] for r in flat]

def unpack(schema,rows):
    if len(rows)!=schema['N']:raise ValueError('columnar row count')
    paths=[tuple(k) for k,_ in schema['constants']]+[tuple(k) for k in schema['columns']]
    if len(set(paths))!=len(paths):raise ValueError('duplicate column path')
    for path in paths:
        if not path or not all(type(x) is str for x in path):raise ValueError('column path')
        if any(path[:n] in paths for n in range(1,len(path))):raise ValueError('overlapping column paths')
    result=[]
    for row in rows:
        if len(row)!=len(schema['columns']):raise ValueError('column count')
        value={}
        for path,item in schema['constants']+list(zip(schema['columns'],row)):
            dst=value
            for key in path[:-1]:dst=dst.setdefault(key,{})
            if type(item) is dict and set(item)=={'$string'}:
                index=item['$string']
                if type(index) is not int or not 0<=index<len(schema.get('strings',[])):raise ValueError('string reference')
                item=schema['strings'][index]
            dst[path[-1]]=item
        result.append(value)
    return result

def original_bytes(value,encoding):
    settings={k:v for k,v in encoding.items() if k!='trailing_newline'}
    return (json.dumps(value,allow_nan=False,**settings)+ ('\n' if encoding['trailing_newline'] else '')).encode()
