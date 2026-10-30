"""Exact separate supplement, then pure source-derived prospective readout."""
from pathlib import Path
import json,hashlib,sys
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H))
def main():
    manifest=json.loads((H/'MANIFEST.json').read_text())['files']
    actual={str(p.relative_to(H)) for p in H.rglob('*') if p.is_file() and p.name!='MANIFEST.json'}
    if actual!=set(manifest) or any(p.is_symlink() for p in H.rglob('*')):raise ValueError('exact_file_set')
    for n,h in manifest.items():
        p=Path(n)
        if p.is_absolute() or '..' in p.parts or hashlib.sha256((H/n).read_bytes()).hexdigest()!=h:raise ValueError('manifest_identity')
    from check import audit
    result=audit();result['manifest_files']=len(manifest)
    print(json.dumps(result,sort_keys=True))
if __name__=='__main__':main()
