# v0.7.0 final release verification

Published 7 October 2026: [East Asian Calligraphy Workbench v0.7.0](https://github.com/styayur/calligraphy-studio/releases/tag/v0.7.0).

Tag `v0.7.0` resolves to **`7b9e997c93bc62ea3dc2247e2ebf414953fd8058`**.
The release PR was squash-merged through the repository's required checks.
Its reviewed source tree matches the tagged commit exactly. The tag and published
assets were not replaced. The README presentation update follows publication in
a separate documentation change.

## Evidence

- [Release PR #23](https://github.com/styayur/calligraphy-studio/pull/23): API, Web, Windows, Android, CodeForge and CodeQL checks passed.
- [CodeForge regression](https://github.com/styayur/calligraphy-studio/actions/runs/37586294890): no new findings against the reviewed baseline; native TypeScript/build and Python verification passed.
- [Verification on the merged release commit](https://github.com/styayur/calligraphy-studio/actions/runs/37586915165): all four platform/API jobs passed, including Android preview package/signature validation.
- [Tagged release build and publication](https://github.com/styayur/calligraphy-studio/actions/runs/37586933261): prepare, API, Windows, Web and publish passed; Android publication was deliberately skipped.
- [Pages deployment](https://github.com/styayur/calligraphy-studio/actions/runs/37586915150): the live demo's build receipt was checked against the release commit and version 0.7.0.

The exact tagged API run passed **93 tests**. TypeScript, deterministic visual and
project integrity tests, Chinese/visual/Japanese browser regressions, Windows
installer/portable payload inspection and actual packaged Electron smoke tests
passed. Licence, provenance, canonical version and package validation passed.
Fresh Git source-archive checks also passed, covering the repaired LF/CRLF receipt
boundary. Runtime dependency audits reported no known vulnerabilities; the five
reviewed development-only warnings remain documented separately.

## Published payloads

| File | Bytes | Signing |
| --- | ---: | --- |
| CalligraphyStudio-Setup-0.7.0-x64.exe | 136409924 | NotSigned |
| CalligraphyStudio-Portable-0.7.0-x64.exe | 136165491 | NotSigned |
| CalligraphyStudio-Web-0.7.0.zip | 25222928 | Not applicable |

Also published: `SHA256SUMS.txt`, `release-manifest.json`,
`windows-build-provenance.json`, `web-build-provenance.json` and
`windows-signing.json`.

After publication, all three GitHub asset SHA-256 digests and sizes were compared
with both the release manifest and SHA256SUMS. They match. Both platform build
receipts report the tagged commit and a clean working tree. No APK is attached;
the manifest explicitly records its omission for unavailable production signing.

## Remaining limitations

Windows packages are unsigned. Installer wizard, shortcuts, visible IME,
upgrade/uninstall human acceptance and physical Android storage/share/lifecycle
acceptance remain unexecuted. Automated Electron testing is not a claim that
those manual checks passed. Japanese typography and historical coverage remain
limited as described in the release notes. Earlier RC evidence is retained in
the implementation, dependency, signing and smoke-test reports.
