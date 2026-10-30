"""Corruption controls for the lossless evidence archive; temporary copies only."""
from pathlib import Path
import hashlib
import importlib.util
import json
import shutil
import tempfile

H = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('reader', H/'verify.py')
reader = importlib.util.module_from_spec(spec)
spec.loader.exec_module(reader)

def read(p):
    return json.loads(p.read_text())

def save(p, value):
    p.write_text(json.dumps(value, ensure_ascii=False, separators=(',',':'))+'\n')

def reseal(p):
    save(p/'MANIFEST.json', {'files':{x.relative_to(p).as_posix():hashlib.sha256(x.read_bytes()).hexdigest()
         for x in p.rglob('*') if x.is_file() and x!=p/'MANIFEST.json'}})

def edit_entries(p, fn):
    index=read(p/'EVIDENCE-INDEX.json');path=p/index['file_shards'][0]
    entries=read(path);fn(entries);save(path,entries);reseal(p)

def edit_index(p, fn):
    path=p/'EVIDENCE-INDEX.json';value=read(path);fn(value);save(path,value);reseal(p)

def first_text(entries):
    return next(e for e in entries if e.get('lines'))

def corrupt_hash(p):
    name=read(p/'EVIDENCE-INDEX.json')['line_shards'][0]['path']
    with (p/name).open('ab') as f:f.write(b' ')

def stale_expanded_hash(p):
    edit_entries(p, lambda e:first_text(e).update(sha256='0'*64))

def traversal(p):
    edit_entries(p, lambda e:first_text(e).update(path='paper-package/../../escape.txt'))

def duplicate_path(p):
    edit_entries(p, lambda e:e[1].update(path=e[0]['path']))

def casefold_path(p):
    edit_entries(p, lambda e:e[1].update(path=e[0]['path'].upper().replace('PAPER-PACKAGE','paper-package')))

def invalid_line(p):
    edit_entries(p, lambda e:first_text(e)['lines'].__setitem__(0, 10**9))

def boolean_line(p):
    edit_entries(p, lambda e:first_text(e)['lines'].__setitem__(0, True))

def missing_component(p):
    edit_index(p, lambda x:x['components'].pop('prospective'))

def component_manifest(p):
    edit_index(p, lambda x:x['components']['prospective'].update(manifest_sha256='0'*64))

def expansion_bound(p):
    edit_index(p, lambda x:x.update(expanded_bytes=25_000_001))

def duplicate_json(p):
    path=p/'EVIDENCE-INDEX.json';text=path.read_text()
    path.write_text('{"schema":"wrong",'+text[1:]);reseal(p)

def link_file(p):
    (p/'extra-link').symlink_to(p/'README.md')

def prefix_collision(p):
    # Preserve this entry's content/hash while making its name an existing parent.
    edit_entries(p, lambda entries:entries[-1].update(path='paper-package/artifact'))

CASES=[('stored_hash',corrupt_hash),('expanded_hash',stale_expanded_hash),
       ('path_traversal',traversal),('duplicate_path',duplicate_path),
       ('casefold_collision',casefold_path),('line_out_of_range',invalid_line),
       ('boolean_line_index',boolean_line),('missing_component',missing_component),
       ('component_manifest_identity',component_manifest),('expansion_limit',expansion_bound),
       ('duplicate_json_key',duplicate_json),('symlink',link_file),('file_directory_collision',prefix_collision)]

def main():
    expected,index=reader.expanded_files(H)
    results=[]
    with tempfile.TemporaryDirectory(prefix='ruu-archive-tests-') as temp:
        root=Path(temp)
        for name, mutate in CASES:
            archive=root/name;shutil.copytree(H,archive);mutate(archive)
            dest=root/(name+'-restored')
            try:
                reader.restore(archive,dest)
            except (ValueError,KeyError,TypeError):
                assert not dest.exists(), 'corruption wrote an output directory'
                assert not (root/'escape.txt').exists()
                results.append({'case':name,'rejected_before_write':True})
            else:
                raise AssertionError('corruption accepted: '+name)
            shutil.rmtree(archive)
        dest=root/'existing';dest.mkdir();sentinel=dest/'keep.txt';sentinel.write_bytes(b'preserve')
        try:reader.restore(H,dest)
        except ValueError:
            assert sentinel.read_bytes()==b'preserve' and list(dest.iterdir())==[sentinel]
            results.append({'case':'existing_destination','rejected_before_write':True})
        else:raise AssertionError('existing destination accepted')
        archive=root/'inside-case';shutil.copytree(H,archive)
        try:reader.restore(archive,archive/'new-evidence')
        except ValueError:
            assert not (archive/'new-evidence').exists()
            results.append({'case':'destination_inside_archive','rejected_before_write':True})
        else:raise AssertionError('inside destination accepted')
        restored=root/'roundtrip';reader.restore(H,restored)
        actual={p.relative_to(restored).as_posix():p.read_bytes() for p in restored.rglob('*') if p.is_file()}
        assert actual==expected
    assert not root.exists()
    print(json.dumps({'passed':True,'negative_control_count':len(results),'controls':results,
        'roundtrip_files':index['file_count'],'roundtrip_byte_identity':True,'temporary_files_removed':True,
        'model_calls':0,'evidence_programs_executed':0},sort_keys=True))

if __name__=='__main__':main()
