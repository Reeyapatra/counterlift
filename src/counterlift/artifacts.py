"""Versioned artifact integrity and aggregate-only publication.

Checksums detect corruption, not a malicious replacement of both files and checksums.
Only load joblib models produced by a trusted operator.
"""
import hashlib
import json
import shutil
import subprocess
from pathlib import Path

from .data import checksum

PUBLIC_FILES = ('manifest.json', 'experiment.json', 'policy_evaluation.csv', 'gain_curves.csv')


def source_identity():
    package = Path(__file__).resolve().parent
    candidate = package.parents[1]
    root = candidate if (candidate / 'pyproject.toml').exists() else None
    digest = hashlib.sha256()
    paths = sorted(package.glob('*.py'))
    if root is not None:
        paths += [root / 'app.py', root / 'pyproject.toml']
    for path in paths:
        digest.update(path.name.encode())
        digest.update(path.read_bytes())
    try:
        if root is None:
            raise subprocess.CalledProcessError(1, 'not a source checkout')
        commit = subprocess.check_output(['git', '-C', str(root), 'rev-parse', '--verify', 'HEAD'], stderr=subprocess.DEVNULL, text=True).strip()
        dirty = bool(subprocess.check_output(['git', '-C', str(root), 'status', '--porcelain'], text=True))
    except (subprocess.CalledProcessError, FileNotFoundError):
        commit, dirty = None, True
    return {'commit': commit, 'dirty': dirty, 'implementation_sha256': digest.hexdigest()}


def seal_run(path):
    path = Path(path)
    hashes = {p.name: checksum(p) for p in sorted(path.iterdir()) if p.is_file() and p.name != 'COMPLETE.json'}
    (path / 'COMPLETE.json').write_text(json.dumps({'schema_version': 1, 'sha256': hashes}, indent=2))


def verify_run(path, public=False):
    path = Path(path)
    marker = json.loads((path / 'COMPLETE.json').read_text())
    if marker.get('schema_version') != 1:
        raise ValueError('Unsupported artifact schema')
    hashes = marker.get('sha256', {})
    required = set(PUBLIC_FILES) if public else set(PUBLIC_FILES) | {'model.joblib', 'audit.sqlite'}
    if not required.issubset(hashes):
        raise ValueError('Incomplete artifact manifest')
    for name, expected in hashes.items():
        if Path(name).name != name or checksum(path / name) != expected:
            raise ValueError(f'Artifact integrity check failed: {name}')
    manifest = json.loads((path / 'manifest.json').read_text())
    if manifest.get('schema_version') != 1 or manifest.get('status') != 'offline_evaluated':
        raise ValueError('Unsupported or unevaluated run')
    return manifest


def export_public(source, destination):
    import tempfile
    source, destination = Path(source), Path(destination)
    verify_run(source)
    if destination.exists():
        raise ValueError('Use a fresh public export directory')
    destination.parent.mkdir(parents=True, exist_ok=True)
    staging = Path(tempfile.mkdtemp(prefix='.export-', dir=destination.parent))
    try:
        for name in PUBLIC_FILES:
            shutil.copyfile(source / name, staging / name)
        seal_run(staging)
        # Public aggregates must be readable by the nonroot app container.
        staging.chmod(0o755)
        for artifact in staging.iterdir():
            artifact.chmod(0o644)
        verify_run(staging, public=True)
        staging.rename(destination)
    finally:
        if staging.exists():
            shutil.rmtree(staging)
