"""Pinned runtime identities from this separately obtained software, not the assessment."""
import hashlib
import io
import json
import stat
import zipfile
from pathlib import Path, PurePosixPath
from .errors import ReviewFailure

PREFIX = 'HIGGS_NEAR_REAL_CAMERA_CHANGE_v0.1.2_CRUCIBLE'
PINS_SHA256 = '30c58d2e90de638859c16cbb04fc2c6b68fd5955c05daf8005b265583d201f5f'

def digest(raw):
    return hashlib.sha256(raw).hexdigest()

def fail(code, message):
    raise ReviewFailure('INTEGRITY_ERROR', code, message)

def pins():
    raw = (Path(__file__).parent / 'data/approved_runtime_pins.json').read_bytes()
    if digest(raw) != PINS_SHA256:
        fail('VERIFIER_PINS', 'Verifier-owned runtime pin set differs from the approved version')
    return json.loads(raw)

def verify_runtime_bytes(raw):
    """Identity, ZIP and member checks all inspect exactly these immutable bytes."""
    expected = pins(); identity = digest(raw)
    if identity not in (expected['original_archive_sha256'], expected['subset_sha256']):
        fail('RUNTIME_IDENTITY', 'Runtime does not match an externally pinned approved archive')
    try:
        with zipfile.ZipFile(io.BytesIO(raw)) as z:
            names = z.namelist(); manifest_name = PREFIX + '/SHA256SUMS.json'
            manifest_raw = z.read(manifest_name)
            if digest(manifest_raw) != expected['original_manifest_sha256']:
                fail('RUNTIME_MANIFEST', 'Runtime source manifest differs from the verifier pin')
            full = json.loads(manifest_raw)['files']
            members = full if identity == expected['original_archive_sha256'] else expected['required_members']
            if len(names) != len(set(names)) or set(names) != {PREFIX + '/' + n for n in members} | {manifest_name}:
                fail('RUNTIME_MEMBERSHIP', 'Runtime members differ from the approved member set')
            for rel, rec in members.items():
                info = z.getinfo(PREFIX + '/' + rel)
                if PurePosixPath(rel).is_absolute() or '..' in PurePosixPath(rel).parts or stat.S_ISLNK(info.external_attr >> 16):
                    fail('RUNTIME_PATH', 'Unsafe runtime member')
                data = z.read(info)
                if digest(data) != rec['sha256'] or len(data) != rec['bytes']:
                    fail('RUNTIME_MEMBER', 'Runtime member differs from approved source bytes')
            for rel, rec in expected['required_members'].items():
                if full.get(rel) != rec:
                    fail('RUNTIME_RELATIONSHIP', 'Subset member relationship differs from pinned original')
    except (zipfile.BadZipFile, KeyError, ValueError) as exc:
        raise ReviewFailure('INTEGRITY_ERROR', 'RUNTIME_ARCHIVE', 'Malformed approved runtime archive') from exc
    return {'sha256': identity, 'kind': 'original' if identity == expected['original_archive_sha256'] else 'approved_runtime_subset',
            'original_archive_sha256': expected['original_archive_sha256'], 'source_manifest_sha256': expected['original_manifest_sha256'],
            'approved_member_set_sha256': PINS_SHA256}

def read_runtime(path):
    try:
        raw = Path(path).read_bytes()
    except OSError as exc:
        raise ReviewFailure('CONFIGURATION_ERROR', 'RUNTIME_UNAVAILABLE', 'Configured runtime is unavailable') from exc
    identity = verify_runtime_bytes(raw)
    return raw, identity

def extract_verified_bytes(raw, destination):
    identity = verify_runtime_bytes(raw)
    with zipfile.ZipFile(io.BytesIO(raw)) as z:
        z.extractall(destination)
    return identity
