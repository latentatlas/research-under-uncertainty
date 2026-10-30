"""Portable data paths and strict JSON helpers. No launcher or provider configuration."""
from pathlib import Path
from .strict_io import read_json as read, file_digest as sha, digest
HERE = Path(__file__).resolve().parents[2] / 'data' / 'transfer'
