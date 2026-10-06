# v0.7.0 release review

Reviewed 6 October 2026. This record supplements the implementation, dependency,
signing and native smoke-test reports; those earlier RC records are retained.

## Repository hygiene

Required source fonts, compressed offline fonts, licences, checksummed manifests,
CODH crops and derivatives, permanent project fixtures, screenshots and audit
documentation are retained. `apps/web/build/releaseMetadata.ts` is build **source**,
not disposable output. No installer, APK, ZIP, keystore, cache or log is tracked.
SQLite WAL/shared-memory sidecars created during testing were removed from the staging area; their ignore rule was added. The ignore rules cover release output, SARIF, local environment overrides and
private signing material, while explicitly retaining the three public Vite mode
configurations. Local build and audit evidence stays under ignored `work/`.

## CodeForge review

Used the current CodeForge Engine 0.2.1 CLI from `styayur/codeforge-engine`:
`doctor`, full `review`, `baseline review --include-fixtures`, explicit
`baseline accept` / `baseline false-positive`, and regression-only `ci` with
configured TypeScript, Python and build verification. No bulk autofix or
application refactor was applied.

The initial review reported 56 diagnostics. The licence-page generator now emits
explicit `html`, `head` and `body` elements with `lang="en"`; generated output was
regenerated and checked. The source review (221 files before adding the portable verification launcher) retains:

| Finding | Count | Reviewed decision |
| --- | ---: | --- |
| Python print / JavaScript console output | 41 | Intentional CLI audit, build or test result output; accepted |
| JavaScript loose null equality | 8 | Deliberately accepts both absent legacy fields and explicit null; accepted |
| Python None-comparison heuristic | 3 | False positives on a default argument, tuple comparison and conditional expression |
| TypeScript/JSX parse diagnostics | 3 | CodeForge grammar gaps; native TypeScript compilation and browser regressions are authoritative |

The reviewed baseline preserves per-finding reasons. Parser gaps and optional
unavailable external tools are not claims of source defects or completed native
analysis. Known findings remain visible; zero findings is not the release goal.

The Windows CodeForge process runner could not resolve `npm` directly despite
the separately passing checks. Its configured commands now use a small Python
launcher that explicitly resolves `npm.cmd` on Windows and `npm` elsewhere;
required verification is rerun rather than counting an unavailable tool as a pass.

## Release-specific fixes and decision

- Android is optional for publication when all signing credentials are absent.
  Partial signing configuration still fails; an included APK must pass production
  signature validation. Preview dispatch never publishes.
- Release receipts accept an explicit Windows/Web-only set and reject an APK or
  Android receipt smuggled into that set. Tests also reject dirty source receipts
  and debug-signed APKs in production mode.
- The publisher refuses to modify an existing release, including an existing
  draft. Every platform checks out the same tag-resolved commit; final hashes and
  provenance accompany the published files.
- v0.7.0 ships unsigned Windows installer/portable and offline Web ZIP. Android
  builds and package validation pass, but the available APK is debug-signed and
  is excluded from publication. No signing identity was created.

## Verification and limits

Python API/security/fixture tests plus four publication-gate cases, TypeScript,
deterministic visual/project tests, Chinese/visual/Japanese browser regressions,
Windows packaging and payload inspection, actual unpacked/portable Electron
renderer smoke tests, Android build/package/signature validation, canonical
licence/provenance/version checks and workflow syntax validation are the release
checks. Clean-commit verification and tagged release-job evidence are required
in addition to the earlier dirty-tree RC runs.

Runtime API and production Web/Desktop dependency audits are clean. Five high
development-only warnings remain under the explicit expiring policy described
in [the dependency audit](DEPENDENCY_AUDIT_0.7.0.md); this is not a zero-warning
development tree.

Windows installer wizard, shortcuts, visible IME and upgrade/uninstall acceptance
remain manual and unexecuted. Android physical-device storage/share/lifecycle
acceptance remains unexecuted. Japanese typesetting and corpus coverage limits
remain as documented in the release notes. No unchecked native test is labelled
passed, and unsigned Windows publication does not imply trusted signing.

Pre-commit CodeForge regression gate: no new findings, ambiguous matches or human-review findings; configured syntax, build and 90 Python tests passed. Raw local JSON/SARIF evidence remains in ignored `work/`. Two superseded baseline fingerprints are retained as resolved history.
