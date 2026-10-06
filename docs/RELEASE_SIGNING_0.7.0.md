# v0.7.0 signing and reproducibility

Local RCs are **unsigned Windows builds** and **debug-signed Android previews**. No private keys were created or committed. Do not distribute the preview APK as a production release. `release/version.json` is canonical: 0.7.0, schema 2, Android code 7, package `io.github.styayur.calligraphystudio`.

## Android

Use an existing production key for upgrade compatibility. The same application ID plus a larger versionCode is insufficient if the signing certificate changes. A debug-signed v0.6 install will not upgrade in place to a differently production-signed v0.7; export projects, uninstall and reinstall if this applies. Do not uninstall without preserving user data.

For a new public signing identity, the release owner may generate a keystore interactively with `keytool -genkeypair -keystore calligraphy-release.jks -alias calligraphy -keyalg RSA -keysize 4096 -validity 10000`. Keep passwords out of command arguments and logs. Back up the keystore, alias and credentials securely; loss can prevent future updates. Existing production identities take precedence. This command is documentation, not an action performed during hardening.

Configure all four environment variables:

| Local variable | GitHub secret |
| --- | --- |
| CALLIGRAPHY_ANDROID_KEYSTORE (absolute private path) | ANDROID_KEYSTORE_BASE64 (encoded contents) |
| CALLIGRAPHY_ANDROID_STORE_PASSWORD | ANDROID_STORE_PASSWORD |
| CALLIGRAPHY_ANDROID_KEY_ALIAS | ANDROID_KEY_ALIAS |
| CALLIGRAPHY_ANDROID_KEY_PASSWORD | ANDROID_KEY_PASSWORD |

Optional public fingerprint: repository variable `ANDROID_CERT_SHA256` becomes `CALLIGRAPHY_ANDROID_CERT_SHA256`. Set it to the approved SHA-256 certificate fingerprint. Production CI omits Android when all signing credentials are absent and fails on partial configuration. When credentials are complete it sets `CALLIGRAPHY_REQUIRE_PRODUCTION_SIGNING=1`, verifies the actual APK and deletes the temporary decoded key even on failure. Preview dispatch permits debug signing but never publishes a release.

Build with Java 21 / SDK 36: `apps/web/android/gradlew assembleRelease` from the Android directory after `npm run cap:sync`. Verify with `python scripts/validate_android_release.py --apk <file> --sdk <sdk> --output android-signing.json`; only previews may add `--allow-preview`. The verifier uses apksigner, checks signature and public certificate, package ID, versionName/code, and optional fingerprint. It rejects Android Debug certificates in production. Version code must increase on the next release.

## Windows

Electron Builder accepts `CSC_LINK` and `CSC_KEY_PASSWORD`; release CI maps `WINDOWS_CSC_LINK` and `WINDOWS_CSC_KEY_PASSWORD`. Automatic certificate discovery is disabled. With no credentials, packages remain unsigned and the release receipt says `NotSigned`. Public trusted Authenticode signing requires an appropriate certificate or configured signing service; self-signed certificates must not be described as publicly trusted signing.

Verify both final files with `Get-AuthenticodeSignature -LiteralPath <exe>` and retain status/public certificate thumbprint in `windows-signing.json`. Unsigned distribution may trigger SmartScreen or organisational policy restrictions. A valid signature does not guarantee instant SmartScreen reputation. Optional signing is supported; no certificate was available for this local run.

## One source revision, honest receipts

Release jobs check out the exact SHA resolved from an existing version tag. They share canonical asset/schema/third-party manifests and normalized dependency lock hashes, including `app/gradle.lockfile`. Vite emits `build-meta.json`: Git SHA, dirty flag, version, timestamp from `SOURCE_DATE_EPOCH` or commit time, Node version, lock hashes and asset/notice hashes. Platform metadata deliberately records Node versions separately while requiring identical commit/locks/receipts/time.

`scripts/package_web.py` sorts ZIP entries and fixes timestamp/modes. Repeated ZIP packaging is byte deterministic. Windows/Android toolchains can contain timestamp/signing variability; we do **not** claim byte-identical installers or APKs across hosts. Integrity is verified through pinned inputs and exact final file hashes.

`scripts/create_release_manifest.py` requires the four canonical filenames (or the three Windows/Web files with explicit `--without-android`), matching platform receipts and signing status, then emits `release-manifest.json` and `SHA256SUMS.txt`. Production rejects dirty source or debug Android signatures. Local review uses explicit `--allow-dirty`, recording `local_rc: true`; its HEAD SHA is a baseline, not a claim that uncommitted edits are in that commit.

v0.7.0 release decision: publish unsigned Windows and offline Web from the clean tagged revision; omit Android because no production signing identity is configured. Native manual checks remain explicitly unverified in the release notes. This supersedes the earlier all-platform RC gate without claiming those checks passed. Existing releases, including drafts, are never overwritten by the workflow. Keep the RC evidence below and in the implementation report as historical audit records.
