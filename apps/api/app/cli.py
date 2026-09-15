from __future__ import annotations

import argparse
import json
from pathlib import Path

from app.config import get_settings
from app.database import Database
from app.providers.font_manifest import FontManifestProvider
from app.providers.mccd import (
    MCCD_LICENSE,
    MCCD_LICENSE_URL,
    MCCD_RIGHTS,
    MCCDLmdbProvider,
    MCCDManifestProvider,
)
from app.providers.nccu_cursive import NCCUCursiveProvider
from app.seed import seed_demo_if_empty
from app.services.embedding_service import EmbeddingService
from app.services.asset_store import AssetStore
from app.services.glyph_importer import GlyphImporter


def _characters(value: str | None) -> set[str] | None:
    if not value:
        return None
    return {character for character in value if not character.isspace()}


def _database_and_assets(args: argparse.Namespace):
    settings = get_settings()
    database = Database(args.db_url or settings.database_url)
    database.create_schema()
    assets_dir = Path(args.assets_dir) if args.assets_dir else settings.assets_dir
    return database, AssetStore(assets_dir, download_remote=getattr(args, "download_remote", False))


def _print_result(result) -> None:
    print(
        f"imported={result.imported} skipped={result.skipped} failed={result.failed}",
        flush=True,
    )
    for error in result.errors:
        print(f"  ! {error}")


def _require_rights(args: argparse.Namespace) -> None:
    if not args.rights_confirmed:
        raise SystemExit(
            "Refusing to import without --rights-confirmed. Review the dataset license and your "
            "intended use before importing."
        )


def import_manifest(args: argparse.Namespace) -> None:
    _require_rights(args)
    database, assets = _database_and_assets(args)
    provider = MCCDManifestProvider(
        manifest_path=args.manifest,
        dataset_root=args.dataset_root,
        dataset_name=args.dataset,
        license_name=args.license,
        license_url=args.license_url,
        rights=MCCD_RIGHTS if args.license == MCCD_LICENSE else {},
        characters=_characters(args.characters),
        limit=args.limit,
    )
    _print_result(GlyphImporter(assets, database).import_provider(provider))


def import_lmdb(args: argparse.Namespace) -> None:
    _require_rights(args)
    database, assets = _database_and_assets(args)
    maps = json.loads(Path(args.maps).read_text(encoding="utf-8")) if args.maps else {}
    provider = MCCDLmdbProvider(
        lmdb_path=args.lmdb,
        attribute_mode=args.attribute_mode,
        maps=maps,
        dataset_name=args.dataset,
        license_name=args.license,
        license_url=args.license_url,
        rights=MCCD_RIGHTS if args.license == MCCD_LICENSE else {},
        characters=_characters(args.characters),
        limit=args.limit,
    )
    _print_result(GlyphImporter(assets, database).import_provider(provider))


def inspect_lmdb(args: argparse.Namespace) -> None:
    try:
        import lmdb
    except ImportError as exc:
        raise SystemExit("Install optional dependency: pip install lmdb") from exc
    path = Path(args.lmdb).resolve()
    env = lmdb.open(str(path), subdir=path.is_dir(), readonly=True, lock=False, max_readers=2)
    try:
        with env.begin(write=False) as txn:
            count = int(txn.get(b"num-samples").decode("ascii"))
            print(f"num-samples={count}")
            for key in sorted(txn.cursor().iternext(values=False)):
                if key.startswith((b"image-", b"label-", b"char-", b"style-", b"dynasty-")):
                    value = txn.get(key)
                    preview = value[:80].decode("utf-8", errors="replace") if value else ""
                    print(f"{key.decode('ascii')} = {preview}")
            print("---")
    finally:
        env.close()


def import_cursive(args: argparse.Namespace) -> None:
    database, assets = _database_and_assets(args)
    provider = NCCUCursiveProvider(
        dataset_root=args.root,
        split=args.split,
        characters=_characters(args.characters),
        limit_per_character=args.limit_per_character,
        include_augmented=args.include_augmented,
    )
    _print_result(GlyphImporter(assets, database).import_provider(provider))


def import_font_manifest(args: argparse.Namespace) -> None:
    database, assets = _database_and_assets(args)
    provider = FontManifestProvider(
        manifest_path=args.manifest,
        characters=_characters(args.characters),
        include_noncommercial=not args.commercial_only,
    )
    _print_result(GlyphImporter(assets, database).import_provider(provider))


def build_embeddings(args: argparse.Namespace) -> None:
    settings = get_settings()
    database = Database(args.db_url or settings.database_url)
    database.create_schema()
    service = EmbeddingService(args.assets_dir or settings.assets_dir)
    with database.session() as session:
        result = service.index(
            session,
            characters=_characters(args.characters),
            limit=args.limit,
            force=args.force,
        )
    print(
        f"model={result.model_name} indexed={result.indexed} skipped={result.skipped} "
        f"failed={result.failed}",
        flush=True,
    )
    for error in result.errors:
        print(f"  ! {error}")


def seed_demo(args: argparse.Namespace) -> None:
    settings = get_settings()
    if args.db_url:
        settings = settings.model_copy(update={"database_url": args.db_url, "seed_demo": True})
    if args.assets_dir:
        settings = settings.model_copy(update={"assets_dir": Path(args.assets_dir)})
    database = Database(settings.database_url)
    database.create_schema()
    print(f"imported={seed_demo_if_empty(database, settings)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="calligraphy-studio")
    subparsers = parser.add_subparsers(dest="command", required=True)

    manifest = subparsers.add_parser("import-mccd-manifest")
    manifest.add_argument("--manifest", required=True)
    manifest.add_argument("--dataset-root")
    manifest.add_argument("--dataset", default="MCCD")
    manifest.add_argument("--license", default=MCCD_LICENSE)
    manifest.add_argument("--license-url", default=MCCD_LICENSE_URL)
    manifest.add_argument("--characters")
    manifest.add_argument("--limit", type=int)
    manifest.add_argument("--download-remote", action="store_true")
    manifest.add_argument("--rights-confirmed", action="store_true")
    manifest.add_argument("--db-url")
    manifest.add_argument("--assets-dir")
    manifest.set_defaults(func=import_manifest)

    lmdb_parser = subparsers.add_parser("import-mccd-lmdb")
    lmdb_parser.add_argument("--lmdb", required=True)
    lmdb_parser.add_argument(
        "--attribute-mode",
        choices=["four-task", "character", "style", "dynasty", "calligrapher"],
        default="four-task",
    )
    lmdb_parser.add_argument("--maps", help="JSON mapping file for indexed attribute labels")
    lmdb_parser.add_argument("--dataset", default="MCCD")
    lmdb_parser.add_argument("--license", default=MCCD_LICENSE)
    lmdb_parser.add_argument("--license-url", default=MCCD_LICENSE_URL)
    lmdb_parser.add_argument("--characters")
    lmdb_parser.add_argument("--limit", type=int)
    lmdb_parser.add_argument("--rights-confirmed", action="store_true")
    lmdb_parser.add_argument("--db-url")
    lmdb_parser.add_argument("--assets-dir")
    lmdb_parser.set_defaults(func=import_lmdb)

    inspect = subparsers.add_parser("inspect-lmdb")
    inspect.add_argument("--lmdb", required=True)
    inspect.set_defaults(func=inspect_lmdb)

    cursive = subparsers.add_parser("import-cursive-nccu")
    cursive.add_argument("--root", required=True)
    cursive.add_argument("--split", default="Test", choices=["Training", "Validation", "Test"])
    cursive.add_argument("--characters")
    cursive.add_argument("--limit-per-character", type=int, default=3)
    cursive.add_argument("--include-augmented", action="store_true")
    cursive.add_argument("--db-url")
    cursive.add_argument("--assets-dir")
    cursive.set_defaults(func=import_cursive)

    fonts = subparsers.add_parser("import-font-manifest")
    fonts.add_argument("--manifest", required=True)
    fonts.add_argument("--characters")
    fonts.add_argument("--commercial-only", action="store_true")
    fonts.add_argument("--db-url")
    fonts.add_argument("--assets-dir")
    fonts.set_defaults(func=import_font_manifest)

    embeddings = subparsers.add_parser("build-embeddings")
    embeddings.add_argument("--characters")
    embeddings.add_argument("--limit", type=int)
    embeddings.add_argument("--force", action="store_true")
    embeddings.add_argument("--db-url")
    embeddings.add_argument("--assets-dir")
    embeddings.set_defaults(func=build_embeddings)

    demo = subparsers.add_parser("seed-demo")
    demo.add_argument("--db-url")
    demo.add_argument("--assets-dir")
    demo.set_defaults(func=seed_demo)
    return parser


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()