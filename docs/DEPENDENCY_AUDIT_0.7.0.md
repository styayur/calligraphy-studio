# v0.7.0 dependency audit

Reviewed 2026-10-06 against npm audit and pip-audit 2.10.1. This is a point-in-time advisory check, not proof that vulnerabilities do not exist. Re-run before publishing. Machine receipts are `work/dependency-audit-rc.json` and `work/api-audit-rc-fixed.json` (local, ignored).

## Remaining five high development findings

All five npm findings aggregate **one** unpatched [braces recursion/stack exhaustion advisory, CVE-2026-93687](https://github.com/advisories/GHSA-vfj7-8cjw-p6xm). The upstream affected braces range is `<=3.0.3`; no patched braces version was available at review. npm proposes Tailwind 4.3.3, a major migration, rather than a compatible braces patch. We retain Tailwind 3 and its existing UI/toolchain.

| npm finding | Installed | npm aggregate vulnerable range | Direct? | Classification / introducing tool |
| --- | --- | --- | --- | --- |
| braces | 3.0.3 | `*` | No | transitive tooling; Tailwind → micromatch / chokidar |
| chokidar | 3.6.0 | `2.0.0 - 3.6.0` | No | build-time watch/glob; Tailwind |
| fast-glob | 3.3.3 | `*` | No | build-time glob; Tailwind |
| micromatch | 4.0.8 | `>=0.2.0` | No | transitive glob parser; Tailwind |
| tailwindcss | 3.4.19 | `<=0.0.0-oxide-insiders.ff2c25f || 2.1.0-canary.1 - 3.4.19` | Yes, dev | build-time CSS generation |

These are real development findings, with **irrelevant production exposure in the verified packages**. Content globs are fixed repository paths (`./index.html`, `./src/**/*.{ts,tsx}`). Imported projects, dataset archives and user text do not become glob expressions. Maliciously modified source/build configuration could exercise the vulnerable tool, so builds still require trusted source. This is not a runtime mitigation for arbitrary use of braces elsewhere.

`release/dependency-policy.json` records this single advisory, the five affected packages and a review expiry of **2026-11-05**. `scripts/audit_dependencies.py` displays the warnings and fails new advisories, runtime findings or expired review. It does not disable npm audit. Remediation: adopt a compatible upstream braces patch when published; otherwise separately evaluate a Tailwind major migration with CSS/browser regressions.

## Fixed during hardening

| Dependency / advisory | Before → after | Exposure and decision |
| --- | --- | --- |
| [sprintf-js CVE-2026-97058](https://github.com/advisories/GHSA-hp3w-g68c-fv3c) | global-agent 3.0.0 → 4.1.3 | electron-builder → @electron/get → global-agent → roarr → sprintf-js 1.1.3. No patched sprintf-js; narrow global-agent override removes roarr/sprintf-js, rather than upgrading Electron/build tooling wholesale. Real HTTP proxy and NO_PROXY download-path probe passes. Eight propagated moderate findings removed. |
| [postcss-selector-parser CVE-2026-104844](https://github.com/advisories/GHSA-rj75-hqrm-r3gf) | 6.1.4 → 7.1.6 | Tailwind → postcss-nested, build-only. Narrow patched parser override; typecheck, CSS build and browser regressions validate compatibility. |
| [source-map-js CVE-2026-93749](https://github.com/advisories/GHSA-68fv-2mgg-jv7q) | 1.2.1 → 1.2.2 | PostCSS build tool; compatible lockfile update. |
| Starlette runtime | 0.47.3 → 1.3.1; FastAPI 0.116.1 → 0.135.4 | Real local API exposure, including Windows StaticFiles UNC paths. Six unique advisories (12 scanner identifiers) fixed. Pydantic/schema retained; all API tests pass. |

The six Starlette advisories are [range DoS](https://github.com/advisories/GHSA-7f5h-v6xp-fcq8), [Host URL injection](https://github.com/advisories/GHSA-86qp-5c8j-p5mr), [UNC/SMB SSRF](https://github.com/advisories/GHSA-wqp7-x3pw-xc5r), [HTTPEndpoint methods](https://github.com/advisories/GHSA-x746-7m8f-x49c), [path authority injection](https://github.com/advisories/GHSA-jp82-jpqv-5vv3), and [URL-encoded form limits](https://github.com/advisories/GHSA-82w8-qh3p-5jfq). Tests exercise filesystem non-resolution, preserved URL authority and form limits; upstream handles the remaining fixes.

## Final scope and enforcement

- Web production npm: **0 known vulnerabilities**; full web tree: **5 high development findings**, zero other findings.
- Desktop full npm tree: **0 known vulnerabilities** after the narrow override. Electron dev package is the shipped runtime binary; full audit is therefore checked, not only `--omit=dev`.
- Resolved API runtime requirements: **0 known vulnerabilities** in pip-audit. The API is optional and is not inside the desktop/APK/ZIP.
- Vite records actual renderer module packages in `build-modules.json` and rejects the five vulnerable tools. They also fail package gates if present; desktop has no production Node dependencies containing them. Notice inventory may deliberately include type-only benign packages; it is not a renderer module inventory.
- Security scanner dependencies are isolated locally in `work/security-venv`; scanner installation does not rewrite runtime dependency pins.

Reproduce: `python scripts/audit_dependencies.py`; in an isolated scanner environment, `python -m pip_audit -r apps/api/requirements.txt`. Formal CI fails if the advisory database is unavailable; an audit error is never interpreted as a clean result.
