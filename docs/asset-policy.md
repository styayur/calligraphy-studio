# Asset and data policy

Calligraphy Studio keeps source assets for reproducibility while excluding runtime and generated data.

## East Asian tiers (schema 2)

`samples/asset-manifest.json` is the canonical asset pack list and release version. All platform builds use `apps/web/public/fonts/asset-manifest.json`, which records its SHA-256. Run `python scripts/validate_assets.py` before packaging.

- **Core:** original Chinese fonts plus five redistributable Yuji fonts. Japanese TTF originals live in `samples/fonts/japanese/yuji/`; lossless gzip runtime copies are generated, checksummed and lazily loaded from `apps/web/public/fonts/`.
- **Historical sample:** 20 legally redistributable CODH source crops, original receipts and explicit CC-BY-SA ink-mask derivatives. Source images: `samples/japanese/historical/sample/`; runtime derivatives: `apps/web/public/japanese/`.
- **Full corpus:** ignored `data/imports/` contains verified archives and import receipts; ignored `storage/assets/` contains content-addressed runtime crops. No startup download, no upstream script execution, no multi-gigabyte release assets.

Importer reads archives in place, validates paths (including Windows paths), symlinks, types, checksums, image dimensions, expansion limits and manifests; streams coordinate CSVs and persists one crop at a time. Checkpoint commits every 100 records make repeated/cancelled imports idempotent. Files use content checksums; glyph identity remains separate so different variants sharing a bitmap coexist. Optional corpus queries are indexed and paginated; browser loads selected pages and images lazily.

Bundling requires explicit `redistribution_allowed=true`. Commercial-only selection/export requires explicit `commercial_use=true`. ND image masks/adaptations are rejected. Share-alike flags, source licences, attribution and checksums survive composition and export. Unknown values remain null. Licence obligations apply to third-party assets independently of the MIT code licence.

Japanese runtime font files use `.ttf.gzip`, not `.gz`: Android AAPT strips/decompresses the latter suffix, breaking a canonical cross-platform path and checksum. Lossless bytes and manifest paths are verified inside the actual APK, web ZIP and Windows ASAR by `validate_package.py` / `validate_desktop_package.cjs`.

## Tracked source assets

| Area | Purpose | Rule |
| --- | --- | --- |
| `samples/fonts/ofl/` | Original OFL font files used to generate glyph assets | Keep license text, source URL, designer, and checksum |
| `samples/fonts/licenses/` | OFL license texts | Keep verbatim and alongside the font record |
| `samples/cursive/raw/` | Limited NCCU cursive test subset | Keep dataset license and source metadata |
| `third_party/hanzi-writer/` | Hanzi Writer/Arphic structural data and license | Preserve modification and redistribution notices |
| `apps/web/public/fonts/` | Browser-ready font derivatives and catalog | Record source font, transform command, and checksum |

## Generated or runtime data

| Path | Status | Rule |
| --- | --- | --- |
| `data/raw/`, `data/processed/` | Generated/import staging | Ignored; rebuild or import rather than commit |
| `data/*.db`, `data/*.sqlite*` | Runtime database | Never commit |
| `storage/assets/` | Runtime glyph/asset store | Never commit |
| `apps/web/dist/` | Generated static build | Release workflow only |
| `apps/desktop/release/` | Generated installer/portable output | Release workflow only |
| `work/` | Test screenshots and temporary artifacts | Never commit |

## Admission checklist

1. Identify the original source and stable version/URL.
2. Verify the exact license and whether redistribution, modification, and commercial use are permitted.
3. Record the author/designer and any required notice.
4. Add the source file under the appropriate tracked directory only when redistribution is allowed.
5. Generate derived assets with a committed script where possible.
6. Add or update the manifest and SHA-256 provenance record.
7. Update `third_party/NOTICE.md`, `docs/FONT_LICENSES.md`, and release packaging when licenses or bundled assets change.

Hashes and source details for the bundled calligraphy fonts are recorded in
[`samples/fonts/provenance.json`](../samples/fonts/provenance.json).
