# Asset and data policy

Calligraphy Studio keeps source assets for reproducibility while excluding runtime and generated data.

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
