"""Check the TMLR submission identity and its byte-identical browsing copies.

Python 3.12 standard library; no network, model requests or scientific code execution.
Use submission/verify.py for the thirteen existing-evidence checks.
"""
from pathlib import Path
import argparse
import hashlib
import json
import runpy
import sys

ROOT = Path(__file__).resolve().parent
PAPER_SHA = '8043ec80b38a4aab1749a98027998066f37bbf3fa4e8270f92ac912f24c7e0e6'
ZIP_SHA = '6fce1da5fa90a97e621d26dd6c053499855ad79e3c59bf1fe7a1cf512a9a6134'


def require(ok, reason):
    if not ok:
        raise ValueError(reason)


def digest(raw):
    return hashlib.sha256(raw).hexdigest()


def regular(path):
    require(path.is_file() and not path.is_symlink(), 'missing or nonregular file')
    return path.read_bytes()


def relative(name):
    require(isinstance(name, str) and bool(name) and '\\' not in name, 'invalid path')
    p = Path(name)
    require(not p.is_absolute() and p.as_posix() == name and
            all(x not in ('.', '..') for x in p.parts), 'unsafe path')
    return p


def check(zip_path=None):
    require(sys.version_info[:2] == (3, 12), 'use Python 3.12')
    binding = json.loads(regular(ROOT / 'SUBMISSION.json'))
    require(binding['schema'] == 'ruu-submission-binding-v1' and
            binding['revision'] == 'v2.0.18' and binding['forum_id'] == 'Lu6hxicGcr' and
            binding['submission_number'] == 13906, 'submission identity')
    paper = binding['paper']
    require(paper == {'path': 'submission/paper/manuscript.pdf', 'bytes': 204150,
                      'sha256': PAPER_SHA}, 'paper binding')
    raw = regular(ROOT / paper['path'])
    require(len(raw) == paper['bytes'] and digest(raw) == PAPER_SHA, 'submitted PDF bytes')
    supplement = binding['supplement']
    require(supplement['sha256'] == ZIP_SHA and supplement['bytes'] == 18459131,
            'submitted ZIP binding')
    base = ROOT / 'submission'
    paths = list(base.rglob('*'))
    require(not base.is_symlink() and not any(p.is_symlink() for p in paths), 'submission symlink')
    files = {p.relative_to(base).as_posix(): p for p in paths if p.is_file()}
    expected = supplement['files']
    require(len(files) == 25 and set(files) == set(expected), 'submitted file set')
    for name, expected_hash in expected.items():
        relative(name)
        require(digest(regular(files[name])) == expected_hash, 'submitted file hash: ' + name)
    # The reader is loaded only after its exact submitted bytes have been verified.
    reader = runpy.run_path(str(base / 'verify.py'), run_name='ruu_storage_reader')
    expanded, index = reader['expanded_files'](base)
    require(len(expanded) == supplement['expanded_file_count'] == 1424, 'expanded file count')
    require(supplement['components'] == {'paper-package': 949, 'prospective': 475}, 'component counts')
    for component, count in supplement['components'].items():
        require(sum(n.startswith(component + '/') for n in expanded) == count, 'component inventory')
    mirrors = binding['browsing_copies']
    browse = ROOT / 'browse'
    paths = list(browse.rglob('*'))
    require(not browse.is_symlink() and not any(p.is_symlink() for p in paths), 'browsing symlink')
    actual = {p.relative_to(ROOT).as_posix() for p in paths if p.is_file()}
    require(actual == set(mirrors) | {'browse/README.md'}, 'browsing file set')
    for name, entry in mirrors.items():
        relative(name)
        require(name == 'browse/' + entry['expanded_path'] and entry['expanded_path'] in expanded,
                'browsing source identity')
        raw = regular(ROOT / name)
        require(raw == expanded[entry['expanded_path']] and digest(raw) == entry['sha256'],
                'browsing source bytes: ' + name)
    zip_checked = zip_path is not None
    if zip_checked:
        raw = regular(zip_path)
        require(len(raw) == supplement['bytes'] and digest(raw) == ZIP_SHA, 'submitted ZIP bytes')
    return {'passed': True, 'revision': binding['revision'], 'submission_number': 13906,
            'submitted_files': len(files), 'expanded_files': len(expanded),
            'browsing_copies': len(mirrors), 'submitted_zip_checked': zip_checked,
            'evidence_checks_run': False, 'model_calls': 0}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--zip', type=Path, help='Optionally verify the exact downloaded supplementary ZIP.')
    args = parser.parse_args()
    try:
        result = check(args.zip)
    except (ValueError, OSError, KeyError, TypeError) as exc:
        print(json.dumps({'passed': False, 'error': str(exc)}))
        return 1
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == '__main__':
    sys.exit(main())
