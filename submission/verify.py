"""Restore exact reviewed evidence from readable UTF-8 line shards, then check it.

Standard library only. No network, provider access or participant-program execution.
The storage representation is lossless; all expanded hashes are independently checked.
"""
from pathlib import Path, PurePosixPath
import argparse
import hashlib
import json
import shutil
import subprocess
import sys
import tempfile

H = Path(__file__).resolve().parent
MAX_FILE = 2_000_000
MAX_ARCHIVE = 20_000_000
MAX_EXPANDED = 25_000_000

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def require(ok, reason):
    if not ok:
        raise ValueError(reason)

def json_bytes(raw):
    def pairs(items):
        result = {}
        for k, v in items:
            require(k not in result, 'duplicate JSON key')
            result[k] = v
        return result
    def constant(value):
        raise ValueError('nonfinite JSON value')
    return json.loads(raw.decode('utf-8'), object_pairs_hook=pairs, parse_constant=constant)

def safe_name(name):
    if not isinstance(name,str) or not name or '\\' in name or not name.isascii():
        return False
    p=PurePosixPath(name)
    return (not p.is_absolute() and str(p)==name and
            all(x not in ('','.','..') and not x.startswith('.') for x in p.parts)
            and all(32<ord(c)<127 for c in name))

def archive_files(root):
    require(root.is_dir() and not root.is_symlink(), 'archive root')
    paths=list(root.rglob('*'))
    require(not any(p.is_symlink() for p in paths), 'symlink')
    files={p.relative_to(root).as_posix():p for p in paths if p.is_file()}
    require(len(files)<=1000 and 'MANIFEST.json' in files, 'archive inventory')
    require(all(safe_name(n) and p.stat().st_nlink==1 and p.stat().st_size<=MAX_FILE for n,p in files.items()), 'unsafe or oversized archive file')
    require(sum(p.stat().st_size for p in files.values())<=MAX_ARCHIVE,'archive byte limit')
    raw={n:p.read_bytes() for n,p in files.items()}
    m=json_bytes(raw['MANIFEST.json'])['files']
    require(set(m)==set(raw)-{'MANIFEST.json'},'exact archive file set')
    require(all(safe_name(n) and sha(raw[n])==h for n,h in m.items()),'archive hash')
    return raw

def expanded_files(root):
    raw=archive_files(root)
    index=json_bytes(raw['EVIDENCE-INDEX.json'])
    require(index['schema']=='lossless-utf8-lines-v1','storage schema')
    require(type(index['file_count']) is int and 0<index['file_count']<=2000,'file count')
    require(type(index['expanded_bytes']) is int and 0<index['expanded_bytes']<=MAX_EXPANDED,'expanded byte bound')
    lines=[]; consumed=set()
    for shard in index['line_shards']:
        name=shard['path'];require(name in raw and name not in consumed,'line shard identity');consumed.add(name)
        data=json_bytes(raw[name])
        require(type(data['start']) is int and type(shard['start']) is int and data['start']==len(lines) and shard['start']==len(lines),'line offsets')
        values=data['lines'];require(isinstance(values,list) and all(isinstance(s,str) and s for s in values),'line data')
        require(type(shard['count']) is int and len(values)==shard['count'],'line count')
        lines.extend(values)
    require(type(index['line_count']) is int and len(lines)==index['line_count'],'total line count')
    entries=[]
    for name in index['file_shards']:
        require(name in raw and name not in consumed,'file shard identity');consumed.add(name)
        part=json_bytes(raw[name]);require(isinstance(part,list),'file shard data');entries.extend(part)
    require(len(entries)==index['file_count'],'expanded inventory count')
    output={};folded=set();total=0
    for e in entries:
        name=e['path']
        require(safe_name(name) and name.split('/')[0] in ('paper-package','prospective'),'expanded path')
        require(name not in output and name.casefold() not in folded,'duplicate expanded path');folded.add(name.casefold())
        require(type(e['bytes']) is int and 0<=e['bytes']<=MAX_FILE,'expanded file size')
        total+=e['bytes'];require(total<=index['expanded_bytes'],'expanded total overflow')
        if 'lines' in e:
            require(set(e)=={'path','bytes','sha256','lines'},'text entry fields')
            ids=e['lines'];require(isinstance(ids,list) and all(type(i) is int and 0<=i<len(lines) for i in ids),'line reference')
            size=0;parts=[]
            for i in ids:
                piece=lines[i].encode('utf-8');size+=len(piece)
                require(size<=e['bytes'],'expanded file overflow');parts.append(piece)
            value=b''.join(parts)
        else:
            require(set(e)=={'path','bytes','sha256','binary'},'binary entry fields')
            require(e['binary'] in raw and e['binary'].endswith('.pdf'),'binary reference')
            value=raw[e['binary']]
        require(len(value)==e['bytes'] and sha(value)==e['sha256'],'expanded file hash')
        output[name]=value
    require(total==index['expanded_bytes'],'expanded total mismatch')
    require(all(str(parent).casefold() not in folded for name in output for parent in PurePosixPath(name).parents if str(parent)!='.'),'file/directory collision')
    for component,expected in index['components'].items():
        require(component in ('paper-package','prospective'),'component name')
        key=component+'/MANIFEST.json';require(sha(output[key])==expected['manifest_sha256'],'component manifest identity')
        manifest=json_bytes(output[key])['files']
        actual={n[len(component)+1:] for n in output if n.startswith(component+'/')}
        require(type(expected['file_count']) is int and len(actual)==expected['file_count'],'component count')
        require(actual==set(manifest)|{'MANIFEST.json'},'component inventory')
        require(all(safe_name(n) and sha(output[component+'/'+n])==h for n,h in manifest.items()),'component hash')
    require(set(index['components'])=={'paper-package','prospective'},'both components required')
    binding=json_bytes(output['paper-package/PROSPECTIVE-BINDING.json'])
    require(binding['manifest_sha256']==sha(output['prospective/MANIFEST.json']),'prospective binding')
    return output,index

def restore(root,dest):
    output,index=expanded_files(root)  # Validate every byte before any output write.
    require(not dest.resolve().is_relative_to(root.resolve()),'destination must be outside archive')
    require(not dest.exists() and not dest.is_symlink(),'destination must not exist')
    dest.mkdir(parents=True)
    try:
        for name,value in output.items():
            p=dest/name;p.parent.mkdir(parents=True,exist_ok=True)
            with p.open('xb') as f:f.write(value)
        require(all(sha((dest/n).read_bytes())==sha(v) for n,v in output.items()),'restored hash')
    except BaseException:
        shutil.rmtree(dest)
        raise
    return index

def run_checks(dest):
    main=dest/'paper-package';pros=dest/'prospective'
    p=subprocess.run([sys.executable,'-I','-B','-S',str(main/'verify_all.py'),
                      '--prospective-dir',str(pros)],cwd=main,capture_output=True,text=True,timeout=900)
    require(p.returncode==0,'evidence checks failed: '+p.stderr[-2200:])
    result=json_bytes(p.stdout.encode())
    require(result['passed'] and len(result['checks'])==13,'thirteen evidence checks')
    return {'passed':True,'evidence_checks':{k:v['passed'] for k,v in result['checks'].items()},
            'paired_correctness':result['checks']['interpretation']['paired_correctness'],
            'evaluated_targets':len(result['checks']['interpretation']['pairs']),
            'main_manifest_members':result['manifest_files'],
            'full_result_sha256':sha(p.stdout.encode()),'new_model_calls':0,
            'new_scientific_samples':0,'participant_programs_executed':0,
            'scope':'Existing-evidence checks and present-host numerical replay; not historical attestation or independent laboratory replication.'}

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--extract-to',type=Path,help='Restore both exact components in a new directory; no evidence programs run.')
    p.add_argument('--archive-only',action='store_true',help='Validate the complete storage and expanded hashes without executing evidence checks.')
    args=p.parse_args()
    if args.extract_to:
        require(not args.archive_only,'choose one mode')
        index=restore(H,args.extract_to.absolute())
        print(json.dumps({'passed':True,'extracted_files':index['file_count'],'expanded_bytes':index['expanded_bytes'],'evidence_checks_run':False}))
    elif args.archive_only:
        _,index=expanded_files(H)
        print(json.dumps({'passed':True,'expanded_files':index['file_count'],'expanded_bytes':index['expanded_bytes'],'evidence_checks_run':False}))
    else:
        with tempfile.TemporaryDirectory(prefix='ruu-reader-') as tmp:
            dest=Path(tmp)/'evidence';index=restore(H,dest);result=run_checks(dest)
        result.update({'expanded_files':index['file_count'],'temporary_evidence_removed':not Path(tmp).exists()})
        print(json.dumps(result,sort_keys=True))

if __name__=='__main__':main()
