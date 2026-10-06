import importlib.util
from pathlib import Path
import pytest

ROOT=Path(__file__).resolve().parents[3]
spec=importlib.util.spec_from_file_location('notice_gate',ROOT/'scripts/validate_third_party.py')
gate=importlib.util.module_from_spec(spec);spec.loader.exec_module(gate)
PUBLIC=ROOT/'apps/web/public'

def test_canonical_notices_and_all_codh_derivative_receipts():
    assert gate.validate_reader(lambda path:(PUBLIC/path).read_bytes())==43
    assert gate.validate_codh()==20

@pytest.mark.parametrize('missing',['LICENSE','fonts/licenses/OFL-yuji-syuku.txt','demo/licenses/nccu-mit.txt','demo/licenses/arphic-public-license.txt'])
def test_missing_or_changed_packaged_licence_fails(missing):
    with pytest.raises(AssertionError):
        gate.validate_reader(lambda path:b'changed licence text' if path==missing else (PUBLIC/path).read_bytes())

def test_relabelled_third_party_manifest_fails():
    with pytest.raises(AssertionError):
        gate.validate_reader(lambda path:b'{"components":[]}' if path=='third-party-manifest.json' else (PUBLIC/path).read_bytes())
