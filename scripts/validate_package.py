"""Check actual ZIP/APK contents against the canonical runtime asset receipt."""
import argparse
import hashlib
import json
import zipfile
from pathlib import Path
from validate_third_party import validate_reader

ROOT = Path(__file__).resolve().parents[1]


def validate(path: Path, prefix: str):
    public = ROOT / 'apps/web/public'
    canonical = json.loads((public / 'fonts/asset-manifest.json').read_text(encoding='utf-8'))
    with zipfile.ZipFile(path) as archive:
        read = lambda file: archive.read(prefix + file)
        notice_count=validate_reader(read)
        metadata=json.loads(read('build-meta.json'))
        assert metadata['version']=='0.7.0' and len(metadata['commit'])==40
        modules=json.loads(read('build-modules.json'))['packages']
        assert not set(modules)&{'braces','chokidar','fast-glob','micromatch','tailwindcss'}
        if json.loads(read('fonts/asset-manifest.json')) != canonical:
            raise ValueError('Packaged canonical manifest differs')
        for font in canonical['fonts']:
            file = font['runtime']['path'].removeprefix('apps/web/public/')
            if hashlib.sha256(read(file)).hexdigest() != font['runtime']['sha256']:
                raise ValueError(f'Packaged font checksum mismatch: {file}')
            read(font['license_text'])
        historical = json.loads(read('japanese/glyphs.json'))
        expected = json.loads((public / 'japanese/glyphs.json').read_text(encoding='utf-8'))
        if historical != expected:
            raise ValueError('Packaged historical metadata differs')
        for glyph in historical:
            if hashlib.sha256(read(glyph['asset']['url'])).hexdigest() != glyph['asset']['checksum']:
                raise ValueError('Packaged historical checksum mismatch')
            read(glyph['source']['license_text'])
        for file in ['LICENSE','THIRD_PARTY_NOTICE.md','licenses/HarfBuzz-COPYING.txt','licenses/harfbuzzjs-MIT.txt']:
            if read(file) != (public / file).read_bytes():
                raise ValueError(f'Packaged licence notice differs: {file}')
    print(f'PASS: {path.name}: schema 2, 8 fonts, 20 historical assets, {notice_count} licence components, build provenance and tooling exclusion ({path.stat().st_size} bytes)')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--apk',type=Path)
    parser.add_argument('--web-zip',type=Path)
    args = parser.parse_args()
    if not args.apk and not args.web_zip: parser.error('Specify --apk or --web-zip')
    if args.apk: validate(args.apk,'assets/public/')
    if args.web_zip: validate(args.web_zip,'')
