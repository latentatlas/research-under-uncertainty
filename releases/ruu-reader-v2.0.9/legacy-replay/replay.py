#!/usr/bin/env python3
"""Local replay entry point. Run with CPython 3.12 -I -B -S."""
import argparse
import ast
import cmath
import copy
from datetime import datetime, timezone
import decimal
import fractions
import hashlib
import json
import math
import os
from pathlib import Path
import resource
import socket
import subprocess
import sys
import sysconfig
import time


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError('manifest duplicate key')
        out[key] = value
    return out


def manifest_check(root):
    manifest = json.loads((root / 'MANIFEST.json').read_text(), object_pairs_hook=pairs)
    if manifest.get('schema') != 'world04-private-workbench-manifest-v1':
        raise ValueError('manifest schema')
    expected = {row['path']: row for row in manifest['files']}
    if len(expected) != len(manifest['files']):
        raise ValueError('manifest repeated path')
    paths = list(root.rglob('*'))
    if any(p.is_symlink() for p in paths):
        raise ValueError('symlinks forbidden')
    actual = {p.relative_to(root).as_posix() for p in paths if p.is_file() and p != root / 'MANIFEST.json'}
    if actual != set(expected):
        raise ValueError('manifest file inventory mismatch')
    for name, row in expected.items():
        path = root / name
        if path.resolve().parent != root.resolve() and root.resolve() not in path.resolve().parents:
            raise ValueError('manifest path traversal')
        if path.stat().st_size != row['bytes'] or sha(path) != row['sha256']:
            raise ValueError('manifest digest mismatch: ' + name)
    return {'passed': True, 'files': len(expected), 'manifest_sha256': sha(root / 'MANIFEST.json')}


def main():
    os.umask(0o077)
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('command', choices=('verify', 'reproduce'))
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    root = Path(__file__).resolve().parent
    output = args.output.resolve() if args.output else None
    if not (sys.implementation.name == 'cpython' and sys.version_info[:2] == (3, 12)):
        raise ValueError('CPython 3.12 required; validated patch version is documented')
    if not (sys.flags.isolated and sys.flags.dont_write_bytecode and sys.flags.no_site):
        raise ValueError('invoke Python with -I -B -S')
    if args.command == 'reproduce' and output is None:
        raise ValueError('reproduce requires a new --output directory')
    if args.command == 'verify' and output is not None:
        raise ValueError('verify writes no output directory')
    if output is not None and (output == root or root in output.parents or output.exists() or not output.parent.is_dir()):
        raise ValueError('output must be new, outside workbench, with an existing parent')
    manifest = manifest_check(root)
    sys.path.insert(0, str(root / 'src'))
    from w04replay.containment import install, controls
    stdlib = {sysconfig.get_path('stdlib'), sysconfig.get_path('platstdlib')}
    policy = install(root, output, stdlib, Path(sys.executable))
    from w04replay.records import write_new
    from w04replay.runner import verify, reproduce
    from transferreplay.runner import verify as transfer_verify, reproduce as transfer_reproduce
    io_checks = controls(root)
    expected_denials = len(policy['denied'])
    verified = verify(root)
    verified["transfer"] = transfer_verify(root)
    if args.command == 'verify':
        print(json.dumps({'passed': True, 'manifest': manifest, 'inputs': verified,
                          'io_controls': io_checks, 'policy': policy}, ensure_ascii=False))
        return 0
    output.mkdir(mode=0o700)
    now = lambda: datetime.now(timezone.utc).isoformat()
    start = time.monotonic()
    write_new(output / 'INTENT.json', {'started_utc': now(), 'manifest': manifest,
               'python_version': sys.version, 'python_executable_sha256': sha(Path(sys.executable)),
               'scope': 'fixed_local_recomputation_no_provider_no_new_trials',
               'io_controls': io_checks, 'input_checks': verified})
    try:
        summary = reproduce(root, output)
        transfer_summary = transfer_reproduce(root, output)
        manifest_check(root)
        if len(policy['denied']) != expected_denials:
            raise ValueError('unexpected denied I/O attempt during replay')
        artifacts = [{'path': p.name, 'sha256': sha(p), 'bytes': p.stat().st_size}
                     for p in sorted(output.iterdir()) if p.is_file()]
        closure = {'passed': True, 'finished_utc': now(), 'elapsed_seconds': time.monotonic() - start,
                   'max_rss_platform_units': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,
                   'max_rss_units': 'bytes on macOS; KiB on Linux',
                   'manifest': manifest, 'artifacts': artifacts, 'io_policy': policy,
                   'new_llm_requests': 0, 'same_host_validation_only': True}
        write_new(output / 'CLOSURE.json', closure)
        print(json.dumps({'passed': True, 'output': str(output), 'pilot': summary['pilot'],
                          'component_cells': summary['component_cells'], 'usage': summary['usage'],
                          'transfer': transfer_summary, 'comparison': summary['comparison'], 'elapsed_seconds': closure['elapsed_seconds']}, ensure_ascii=False))
        return 0
    except Exception as exc:
        write_new(output / 'ERROR.json', {'passed': False, 'failed_utc': now(),
                  'type': type(exc).__name__, 'error': str(exc),
                  'elapsed_seconds': time.monotonic()-start, 'io_policy': policy})
        raise


if __name__ == '__main__':
    try:
        raise SystemExit(main())
    except Exception as exc:
        print(json.dumps({'passed': False, 'type': type(exc).__name__, 'error': str(exc)}, ensure_ascii=False))
        raise SystemExit(1)
