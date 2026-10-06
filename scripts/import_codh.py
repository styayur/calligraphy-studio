"""Pinned authoritative archive download and incremental local import.

Use --url with --sha256 to download; or an offline manifest of archives/crops.
No extraction, upstream scripts, or startup downloads. Retry safely after Ctrl+C.
"""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'apps/api'))
from app.database import Database
from app.config import get_settings
from app.providers.codh import CODHKuzushijiProvider
from app.services.asset_store import AssetStore
from app.services.glyph_importer import GlyphImporter


def download(url: str, checksum: str, destination: Path):
    import re
    def authoritative(value):
        parsed = urlparse(value)
        return parsed.scheme == 'https' and parsed.hostname == 'codh.rois.ac.jp' and re.fullmatch(r'/char-shape/dataset/v2/[A-Za-z0-9_-]+\.zip',parsed.path)
    if not authoritative(url) or not re.fullmatch('[0-9a-f]{64}',checksum):
        raise ValueError('Require official CODH v2 URL and reviewed SHA256')
    if destination.is_file() and hashlib.file_digest(destination.open('rb'),'sha256').hexdigest() == checksum:
        return
    destination.parent.mkdir(parents=True,exist_ok=True)
    partial = destination.with_suffix('.zip.part')
    digest, size = hashlib.sha256(), 0
    try:
        with urlopen(Request(url,headers={'User-Agent':'CalligraphyStudio/0.7'}),timeout=60) as response, partial.open('wb') as output:
            if not authoritative(response.url):
                raise ValueError('Unexpected download redirect')
            while chunk := response.read(1024*1024):
                size += len(chunk)
                if size > 10 * 1024**3:
                    raise ValueError('Archive exceeds 10 GB')
                output.write(chunk); digest.update(chunk)
        if digest.hexdigest() != checksum:
            raise ValueError('Downloaded archive checksum mismatch')
        partial.replace(destination)
    finally:
        if partial.exists(): partial.unlink()


def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--manifest',type=Path)
    parser.add_argument('--url'); parser.add_argument('--sha256')
    parser.add_argument('--book-id'); parser.add_argument('--work')
    parser.add_argument('--characters'); parser.add_argument('--limit',type=int)
    parser.add_argument('--db-url'); parser.add_argument('--assets-dir',type=Path)
    args=parser.parse_args()
    if args.limit is not None and args.limit < 1: parser.error('--limit must be positive')
    if args.url:
        if not args.sha256: parser.error('--url requires --sha256')
        filename=Path(urlparse(args.url).path).name
        archive=ROOT/'data/imports'/filename
        download(args.url,args.sha256,archive)
        receipt=archive.with_suffix('.json')
        books={args.book_id:{'work':args.work,'culture':{'writing_tradition':'Japanese','source_collection':'NIJL / CODH'}}} if args.book_id else {}
        receipt.write_text(json.dumps({'schema_version':2,'dataset_version':'v2','archives':[{'file':filename,'sha256':args.sha256,'books':books}]},ensure_ascii=False,indent=2),encoding='utf-8')
        args.manifest=receipt
    if not args.manifest: parser.error('Specify --manifest or --url and --sha256')
    settings=get_settings()
    database=Database(args.db_url or settings.database_url); database.create_schema()
    provider=CODHKuzushijiProvider(args.manifest,characters=set(args.characters) if args.characters else None,limit=args.limit)
    try:
        result=GlyphImporter(AssetStore(args.assets_dir or settings.assets_dir),database).import_provider(provider)
    except KeyboardInterrupt:
        print('Cancelled. Committed checkpoints remain; repeat the same command to resume.')
        return 130
    print(result.model_dump_json(indent=2))
    return int(bool(result.failed))


if __name__=='__main__':
    raise SystemExit(main())
