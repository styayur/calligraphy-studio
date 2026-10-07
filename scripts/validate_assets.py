"""Offline licence/provenance gate used by every platform's CI and release."""
import gzip
import hashlib
import json
import re
import tomllib
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]


def main():
    canonical=ROOT/'samples/asset-manifest.json'
    manifest=json.loads(canonical.read_text(encoding='utf-8'))
    runtime=ROOT/'apps/web/public'
    catalog=json.loads((runtime/'fonts/catalog.json').read_text(encoding='utf-8'))
    packed=json.loads((runtime/'fonts/asset-manifest.json').read_text(encoding='utf-8'))
    if manifest['schema_version']!=2 or packed['schema_version']!=2: raise ValueError('Schema version mismatch')
    if packed['canonical_sha256']!=hashlib.sha256(canonical.read_text(encoding='utf-8').encode('utf-8')).hexdigest(): raise ValueError('Stale canonical runtime manifest')
    originals={}
    for pack in manifest['font_packs']:
        file=ROOT/'samples'/pack
        for entry in json.loads(file.read_text(encoding='utf-8'))['fonts']:
            raw=(file.parent/entry['path']).read_bytes()
            if hashlib.sha256(raw).hexdigest()!=entry['sha256']: raise ValueError('Original font checksum mismatch')
            if entry['rights']['redistribution_allowed'] is not True: raise ValueError('Non-redistributable font in core')
            originals[entry['id']]=entry
    if set(originals)!={font['id'] for font in catalog}: raise ValueError('Catalog packs differ')
    for entry in catalog:
        source=originals[entry['id']]
        for field in ('sha256','source_role','language','locale','writing_tradition','license','original_sha256'):
            if entry.get(field) != source.get(field): raise ValueError(f'Catalog source metadata differs: {entry["id"]}.{field}')
        if entry.get('source_role') == 'coverage-fallback':
            if (entry.get('language'),entry.get('locale'),entry.get('writing_tradition'),entry.get('orthography')) != ('ja','ja-JP','Japanese','Japanese'):
                raise ValueError('Coverage fallback must remain Japanese / ja-JP')
            if entry.get('license') != 'OFL-1.1' or not entry.get('original_sha256'):
                raise ValueError('Coverage fallback lost upstream licence/provenance')
        data=(runtime/'fonts'/entry['path']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=entry['runtime_sha256']: raise ValueError('Runtime font checksum mismatch')
        if entry['renderer']=='harfbuzz' and hashlib.sha256(gzip.decompress(data)).hexdigest()!=entry['sha256']: raise ValueError('Source/runtime Japanese font differs')
        if not (runtime/entry['license_text']).is_file(): raise ValueError('Missing independently bundled font licence')
    original_sample=json.loads((ROOT/'samples/japanese/historical/sample/manifest.json').read_text(encoding='utf-8'))
    for item in original_sample['assets']:
        data=(ROOT/'samples/japanese/historical/sample'/item['file']).read_bytes()
        if hashlib.sha256(data).hexdigest()!=item['sha256']: raise ValueError('CODH original crop checksum mismatch')
    glyphs=json.loads((runtime/'japanese/glyphs.json').read_text(encoding='utf-8'))
    if len(glyphs)!=len(original_sample['assets']): raise ValueError('Historical sample count mismatch')
    for g in glyphs:
        source=g['source']
        if source['license']!='CC-BY-SA-4.0' or source['rights']['share_alike_required'] is not True: raise ValueError('Lost share-alike licence')
        if not source['attribution'] or '10.20676/00000340' not in source['attribution']: raise ValueError('Lost CODH DOI')
        if not (runtime/source['license_text']).is_file(): raise ValueError('Missing historical licence text')
        if hashlib.sha256((runtime/g['asset']['url']).read_bytes()).hexdigest()!=g['asset']['checksum']: raise ValueError('Historical derivative checksum mismatch')
        if g['metadata']['derivative_license']!=source['license']: raise ValueError('Derived crop relabelled')
    for directory in ['apps/web','apps/desktop']:
        if json.loads((ROOT/directory/'package.json').read_text(encoding='utf-8'))['version']!=manifest['release']: raise ValueError('Platform release mismatch')
    if tomllib.loads((ROOT/'apps/api/pyproject.toml').read_text(encoding='utf-8'))['project']['version'] != manifest['release']: raise ValueError('API release mismatch')
    android=(ROOT/'apps/web/android/app/build.gradle').read_text(encoding='utf-8')
    if re.search(r'versionName "([^"]+)"',android).group(1) != manifest['release']: raise ValueError('Android release mismatch')
    for path in ['LICENSE','THIRD_PARTY_NOTICE.md']:
        if not (runtime/path).is_file(): raise ValueError('Missing bundled licence boundary notice')
    for path in ['licenses/HarfBuzz-COPYING.txt','licenses/harfbuzzjs-MIT.txt']:
        if not (runtime/path).is_file(): raise ValueError('Missing shaper software licence')
    size=sum(path.stat().st_size for path in runtime.rglob('*') if path.is_file())
    japanese=sum((runtime/'fonts'/entry['path']).stat().st_size for entry in catalog if entry.get('language')=='ja')
    print(json.dumps({'schema_version':2,'fonts':len(catalog),'historical_sample':len(glyphs),'public_bytes':size,'japanese_font_bytes':japanese,'sample_bytes':sum(path.stat().st_size for path in (runtime/'japanese').rglob('*') if path.is_file())},indent=2))


if __name__=='__main__': main()
