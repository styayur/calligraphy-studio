# v0.7.1 — Japanese Kanji coverage

This release adds **Klee One Regular** as an independent modern Japanese handwriting candidate and a small, Japanese-only **Source Han Serif JP derived subset** as a visibly labelled coverage fallback. Yuji remains the primary calligraphy source; historical CODH samples remain a separate category. Strict Japanese mode never silently substitutes Chinese glyphs.

The reproducible [coverage benchmark](https://github.com/styayur/calligraphy-studio/blob/v0.7.1/docs/JAPANESE_COVERAGE.md) measures JIS X 0213 Kanji cmap coverage at **6,745/10,051 with Yuji alone** and **10,051/10,051 with the combined Japanese library**. Jōyō, Jinmeiyō, JIS X 0208 Kanji and the reviewed project corpus are also complete in the combined benchmark. These figures do not claim complete Japanese typography, historical coverage, IVS support or aesthetic correctness.

The fonts are redistributed under **SIL OFL 1.1**. Their upstream versions, checksums, licences, provenance and reproducible fallback subset recipe are recorded in the source manifests and offline package notices. Existing v0.7.0 projects remain readable; the project schema remains version 2.

Downloads include the Windows x64 installer and portable build, offline Web ZIP, production-signed Android APK, SHA256SUMS.txt and build/signing receipts. All packages come from the same tagged commit. The Windows binaries remain **unsigned** and may prompt SmartScreen. The Android APK is signed with the persistent release identity; its certificate fingerprint is in the signing receipt and [recovery guidance](https://github.com/styayur/calligraphy-studio/blob/v0.7.1/docs/RELEASE_SIGNING_0.7.1.md).

Automated browser, API, Windows native renderer, Android build/signature, package and licence checks passed. Physical Android storage/share/lifecycle testing and the Windows installer wizard, shortcuts, upgrade/uninstall and visible IME acceptance remain manual validation gaps.
