"""Limited, source-referenced orthographic labels, never text substitution."""
import json
from app.config import PROJECT_ROOT
from app.domain import unicode_script

PAIRS = json.loads((PROJECT_ROOT / 'samples/japanese/orthography.json').read_text(encoding='utf-8'))['pairs']
PAIRS = {new: old for new,old in PAIRS.items() if new != old}


def japanese_variant(character: str, configured_type: str | None):
    if configured_type == 'hentaigana':
        return ('hentaigana' if unicode_script(character) == 'Hiragana' else 'font-alternate'), None
    if character in PAIRS:
        return 'shinjitai', character
    for new,old in PAIRS.items():
        if character == old:
            return 'kyujitai', new
    return configured_type, None
