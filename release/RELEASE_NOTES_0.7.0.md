# v0.7.0 — East Asian Calligraphy Workbench

Chinese calligraphy remains supported. Japanese is the first expansion beyond Chinese; other East Asian traditions are not shipped in this release.

- Separate Unicode semantic identity from visual glyph variants and cultural provenance.
- Add five Yuji 3.002 fonts under OFL 1.1, including explicit Akari/Akebono hentaigana variants. Fonts are not historical manuscripts.
- Add HarfBuzz Japanese shaping, mixed kanji/kana and glyph-cell horizontal/vertical composition.
- Add 20 CODH v2 historical crops and attributed ink-mask derivatives under CC BY-SA 4.0; preserve source occurrences and unknown cultural facts. Full corpus remains an optional verified local import.
- Keep Chinese/Japanese candidate traditions isolated by default; cross-tradition exploration is explicit.
- Preserve licence, rights, attribution, Unicode/variant identity and checksums in project and artwork exports.
- Migrate project/database schema v1 → v2; permanent fixtures test semantic and rights integrity across save/reload/export. Back up SQLite/projects before upgrading; downgrade by restoring backups.
- Packages share a canonical asset/third-party manifest, offline licence viewer, version checks and build provenance. No cloud account is required.

## Security and release status

Production web/desktop npm and resolved API dependency audits are clean in the recorded audit. Starlette/FastAPI runtime updates fix six unique API advisories; narrow global-agent, PostCSS parser and source-map updates fix additional toolchain findings. Five development dependency findings trace to the unpatched braces stack-exhaustion advisory in Tailwind 3 tooling; they are retained, scoped and documented in `docs/DEPENDENCY_AUDIT_0.7.0.md`. No vulnerable tooling enters renderer bundles or packaged application dependencies. This does not mean the entire development tree has zero vulnerabilities.

This release publishes the **Windows x64 installer**, **Windows x64 portable executable** and **offline Web ZIP**, with `SHA256SUMS.txt`, build provenance and signing receipts. Windows binaries are **unsigned** and may trigger SmartScreen or organisational restrictions.

**No Android APK is published for v0.7.0.** The Android build and package checks pass locally, but only debug preview signing is available. Production signing and physical Android storage/share/lifecycle acceptance remain outstanding. The automated Windows checks launch the actual unpacked and portable applications; installer wizard, shortcuts, upgrade/uninstall and visible IME acceptance remain unverified. These limitations are disclosed rather than treated as passed.

Conditional signing and verification are documented in [signing guidance](https://github.com/styayur/calligraphy-studio/blob/v0.7.0/docs/RELEASE_SIGNING_0.7.0.md). A production APK is accepted only with complete private signing configuration and successful signature validation; missing credentials omit Android, and partial credentials fail the release.

## Known limitations

Japanese composition is per glyph cell. Full kinsoku shori, advanced punctuation/orientation rules, connected-kana continuity, tate-chū-yoko, arbitrary IVS and comprehensive historical orthography are not implemented. The sample is not complete kuzushiji coverage or proof of historical authenticity. Download resume restarts the download; local import checkpoints are repeatable. Large export ZIPs assemble in browser memory. Canvas/FreeType antialiasing can vary across platforms.

See `docs/MIGRATIONS.md`, `docs/RELEASE_SMOKE_TEST_0.7.0.md` and the release-readiness section of `docs/IMPLEMENTATION_REPORT_0.7.0.md` for exact executed checks, remaining manual tests, package sizes and signing status.
