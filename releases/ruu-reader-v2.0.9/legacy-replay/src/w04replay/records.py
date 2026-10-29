"""Strict records and the historical canonical JSON identity convention."""
import hashlib
import json


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(',', ':'),
                      ensure_ascii=False, allow_nan=False).encode('utf-8')


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _pairs(items):
    out = {}
    for key, value in items:
        if key in out:
            raise ValueError('duplicate JSON key')
        out[key] = value
    return out


def _constant(value):
    raise ValueError('nonfinite JSON constant')


def loads(text):
    return json.loads(text, object_pairs_hook=_pairs, parse_constant=_constant)


def read(path):
    return loads(path.read_text(encoding='utf-8'))


def write_new(path, value):
    import os
    with path.open('x', encoding='utf-8') as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write('\n')
        stream.flush()
        os.fsync(stream.fileno())
