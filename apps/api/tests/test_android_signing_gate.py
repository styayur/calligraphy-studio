"""Keep runner SDK drift from changing publication signature validation."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace

import pytest

ROOT = Path(__file__).resolve().parents[3]
spec = importlib.util.spec_from_file_location('android_gate', ROOT / 'scripts/validate_android_release.py')
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


@pytest.mark.parametrize('certificate_output', [
    'Signer #1 certificate DN: CN=Android Debug\nSigner #1 certificate SHA-256 digest: ' + 'a' * 64 + '\n',
    'Unrecognised certificate output\n',
])
def test_pinned_sdk_and_fail_closed_signing(tmp_path, monkeypatch, certificate_output):
    (tmp_path / 'build-tools/36.0.0').mkdir(parents=True)
    (tmp_path / 'build-tools/99.0.0').mkdir()
    monkeypatch.delenv('CALLIGRAPHY_ANDROID_CERT_SHA256', raising=False)

    def run(command, **kwargs):
        assert Path(command[0]).parent.name == '36.0.0'
        output = certificate_output if 'apksigner' in Path(command[0]).name else (
            "package: name='io.github.styayur.calligraphystudio' versionCode='7' versionName='0.7.0'"
        )
        return SimpleNamespace(stdout=output)

    monkeypatch.setattr(gate.subprocess, 'run', run)
    with pytest.raises(ValueError, match='Debug-signed|Unrecognised'):
        gate.validate(tmp_path / 'preview.apk', tmp_path)
    if certificate_output.startswith('Signer #1'):
        assert gate.validate(tmp_path / 'preview.apk', tmp_path, allow_preview=True)['production_ready'] is False
