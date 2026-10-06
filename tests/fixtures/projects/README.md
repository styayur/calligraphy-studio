# Frozen v2 semantic regression fixtures

Six small, inspectable projects cover legacy Chinese, v2 Chinese, modern Japanese, Akari/Akebono hentaigana, CODH historical provenance and shared-codepoint Chinese/Japanese forms. Assets are **synthetic one-pixel test rasters**, not authentic glyph reproductions. Source receipts are retained only to test metadata preservation. Mixed-CJK Chinese regional records are explicitly synthetic fixtures, not claims about bundled font locales.

`schema-v2.json` freezes the current API project schema. Tests compare it with the generated Pydantic schema: changes require intentional compatibility review. Do not regenerate this snapshot merely to make a regression pass.

Both TypeScript and Python load → migrate → serialize → reload these fixtures. TypeScript exports/parses the real attribution manifest and ZIP; Python exercises project API persistence. Assertions cover the complete identity, variant, source/rights, provenance, metadata and asset checksum, so visually unchanged but stripped projects fail.
