"""Publication gates must reject accidental preview APKs and dirty receipts."""
import hashlib
import importlib.util
import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('release_manifest', ROOT / 'scripts/create_release_manifest.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.fixture
def release_files(tmp_path, monkeypatch):
    def digest(path):
        return hashlib.sha256((ROOT / path).read_text(encoding='utf-8').replace('\r\n', '\n').encode()).hexdigest()
    receipt = {
        'commit': 'release-test', 'version': '0.7.0', 'working_tree_dirty': False,
        'build_timestamp': '2026-10-06T00:00:00Z',
        'locks': {key: digest(path) for key, path in {
            'web': 'apps/web/package-lock.json', 'desktop': 'apps/desktop/package-lock.json',
            'python': 'apps/api/requirements.txt', 'android': 'apps/web/android/app/gradle.lockfile',
        }.items()},
        'asset_manifest_sha256': digest('samples/asset-manifest.json'),
        'third_party_manifest_sha256': digest('third_party/manifest.json'),
    }
    for platform in ['windows', 'web', 'android']:
        (tmp_path / f'{platform}-build-provenance.json').write_text(json.dumps(receipt))
    (tmp_path / 'windows-signing.json').write_text('[]')
    (tmp_path / 'android-signing.json').write_text(json.dumps({'version': '0.7.0', 'production_ready': False}))
    for name in ['Setup-0.7.0-x64.exe', 'Portable-0.7.0-x64.exe', 'Web-0.7.0.zip', 'Android-0.7.0.apk']:
        (tmp_path / f'CalligraphyStudio-{name}').write_bytes(b'test payload')
    monkeypatch.setattr(gate.subprocess, 'check_output', lambda *a, **kw: 'release-test')
    monkeypatch.setattr(sys, 'argv', ['manifest', '--directory', str(tmp_path), '--commit', 'release-test'])
    return tmp_path


def test_preview_apk_rejected(release_files):
    with pytest.raises(AssertionError, match='debug-signed'):
        gate.main()


def test_omission_flag_cannot_smuggle_apk(release_files, monkeypatch):
    monkeypatch.setattr(sys, 'argv', sys.argv + ['--without-android'])
    with pytest.raises(AssertionError, match='Android files must be omitted'):
        gate.main()


@pytest.mark.parametrize('dirty', [False, True])
def test_windows_web_release_requires_clean_receipts(release_files, monkeypatch, dirty):
    for path in release_files.iterdir():
        if 'android' in path.name.lower():
            path.unlink()
    monkeypatch.setattr(sys, 'argv', sys.argv + ['--without-android'])
    receipt_path = release_files / 'web-build-provenance.json'
    receipt = json.loads(receipt_path.read_text())
    receipt['working_tree_dirty'] = dirty
    receipt_path.write_text(json.dumps(receipt))
    if dirty:
        with pytest.raises(AssertionError, match='Dirty source'):
            gate.main()
    else:
        gate.main()
        result = json.loads((release_files / 'release-manifest.json').read_text())
        assert len(result['assets']) == 3
        assert result['signing']['android']['published'] is False
        assert len((release_files / 'SHA256SUMS.txt').read_text().splitlines()) == 3
