"""Portable pure reader support; no runtime, account or private world access."""
from pathlib import Path
from strict_io import canonical,digest,read_json,loads,file_digest as sha
HERE=Path(__file__).resolve().parent
MODELS=('gpt-6-astra','gpt-6.1-sol')
def profile(model):
    if model not in MODELS:raise ValueError('unsupported model')
    return dict(model=model,reasoning_effort='max',service_tier='fast',mode='single_agent')
