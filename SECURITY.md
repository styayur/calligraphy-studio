# Security Policy

## Supported versions

Security fixes target the latest release and the current `main` branch. Older preview builds may receive compatibility guidance only.

## Report privately

Do not report exploitable issues in a public issue. Use GitHub private vulnerability reporting:

https://github.com/styayur/calligraphy-studio/security/advisories/new

Include the affected version/platform, reproduction steps, impact, and any proof-of-concept details needed to verify the report. Remove private documents, personal text, credentials, local paths, and imported project files.

## Scope

Relevant issues include archive/path traversal, unsafe project import, arbitrary file access, local API exposure, browser storage corruption, dependency compromise, release-artifact substitution, and export data leakage.

The web/PWA and Android builds process projects locally. The optional FastAPI service is for local glyph imports and should not be exposed as a public service without an explicit deployment review.
