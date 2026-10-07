# 0.7.0 migration notes

Before upgrading, back up project JSON and the local SQLite database. Existing releases and v0.6.0 download links are retained.

- **Project schema 1 → 2:** loading keeps glyph IDs, transforms, canvas, text and existing source/provenance. Missing semantic identity is synthesized from exact text/codepoints; unverified locale/language and rights become null. New files save as version 2. Old applications should not be used to resave v2 files because they may discard new fields.
- **Database schema 1 → 2:** startup runs `app/migrations.py`. SQLite adds cultural/identity columns, backfills text identity without guessing culture, and transactionally rebuilds the glyph table to replace codepoint-only uniqueness. IDs, foreign keys, project payloads and embedding references are retained and checked. Subsequent starts are repeatable. Databases with a future schema are rejected. SQLite migration is regression-tested; PostgreSQL ALTER path is present but not integration-tested.
- **API compatibility:** existing character search, glyph representation, metadata default (Chinese), project endpoints and original provenance values remain. Additional cultural filters are optional. `/api/meta?writing_tradition=Japanese` or `*` expands metadata; `mode=cross-tradition` is explicit.
- **Canonical assets:** `samples/asset-manifest.json` / runtime receipt use schema 2 and release 0.7.0 on all platforms. Chinese assets are retained; installed optional corpora stay local.
- **Caches:** existing Visual Profile content/version keys remain valid. Candidate page cache includes cultural policy, layout direction and filters. Historical/font checksums invalidate content-derived profiles when an asset changes.
- **Exports:** historical adaptations produce attribution ZIPs; long-roll manifests use schema 2. Unknown rights are never promoted to affirmative permission. Commercial-only mode excludes unknown/non-commercial assets.

Do not downgrade a migrated database in place. Restore the pre-upgrade backup to run a previous release.

The database migration carries forward provider-level Chinese language/tradition facts for the existing named NCCU, OFL Chinese font, MCCD and Hanzi Writer packs. It does not infer language from shared Han characters or assign an unverified Chinese regional locale. Other legacy source metadata remains unknown.
