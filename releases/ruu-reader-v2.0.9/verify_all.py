"""All local reader checks. Standard library, no provider/network/new sample.
Temporary numerical outputs are outside this bundle and removed after checking.
"""
from pathlib import Path
import sys,json,subprocess,tempfile,hashlib,time,argparse
H=Path(__file__).resolve().parent

def run(script,*args):
    p=subprocess.run([sys.executable,'-I','-B','-S',str(H/script),*map(str,args)],cwd=H,text=True,capture_output=True)
    if p.returncode:raise RuntimeError(script+': '+p.stderr[-2500:]+' '+p.stdout[-2500:])
    d=json.loads(p.stdout);assert d.get('passed') is True,(script,d)
    print(json.dumps({'check':script,'passed':True}),file=sys.stderr,flush=True)
    return d

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--followup-only','--scalar-only',dest='followup_only',action='store_true',help='Exact tree, final-table derivation, bound-label lookup and follow-up counts; no older physics/acquisition replay. --scalar-only is a compatibility alias.')
    args=parser.parse_args()
    start=time.monotonic();manifest=json.loads((H/'MANIFEST.json').read_text())['files']
    actual={p.relative_to(H).as_posix() for p in H.rglob('*') if p.is_file() and p!=H/'MANIFEST.json'}
    if actual!=set(manifest) or any(p.is_symlink() for p in H.rglob('*')):raise ValueError('exact_file_set')
    for name,h in manifest.items():
        if hashlib.sha256((H/name).read_bytes()).hexdigest()!=h:raise ValueError('manifest_hash:'+name)
    reports={'artifact/followup/check.py':run('artifact/followup/check.py'),
             'artifact/followup/breakdown.py':run('artifact/followup/breakdown.py')}
    if args.followup_only:
        print(json.dumps({'passed':True,'mode':'followup-only','manifest_files':len(manifest),'checks':reports,'new_samples':0,'model_calls':0,'physics_runs':0,'older_numerical_checks_rerun':False},sort_keys=True))
        return
    for script in ('artifact/check.py','artifact/numeric_constants.py','artifact/protocol/check.py','artifact/interface_audit.py','artifact/pilot_sensitivity.py','artifact/menu_replay.py','artifact/acquisition/replay.py'):
        reports[script]=run(script)
    with tempfile.TemporaryDirectory(prefix='decision-record-reader-') as temp:
        reports['legacy-replay']=run('legacy-replay/replay.py','reproduce','--output',Path(temp)/'output')
    print(json.dumps({'passed':True,'manifest_files':len(manifest),'checks':reports,'wall_seconds':time.monotonic()-start,'new_samples':0,'model_calls':0,'independent_laboratory':False},sort_keys=True))
if __name__=='__main__':main()
