# v0.7.0 native acceptance

Automated renderer tests do not establish physical-device behaviour. Record tester, date, hardware/OS/WebView version, exact SHA256SUMS entry, signing certificate, result and evidence for each manual run. Retain exported projects/attribution ZIPs. Start with backed-up user drafts; use a test installation/profile.

## Automated locally

`scripts/test_windows_native.py --exe <unpacked-or-portable-exe> --output <receipt.json>` launches the actual packaged executable with an isolated test profile and hidden CDP switch. It checks app:// offline loading, version, licence viewer, Chinese/Japanese font composition, legacy/Japanese fixture save/reopen, Yuji modern and hentaigana candidates, JSON/PNG export, and CODH provenance. This is actual Electron execution, not a browser screenshot presented as native evidence. The separate package gate extracts final Setup and Portable payloads and checks their ASAR assets/licences plus Electron/Chromium notices.

Python tests cover schema migration, all six fixture round trips, CJK policy, deterministic shaping plans, rights/export metadata and hostile corpus import. Browser suites cover Chinese workbench, profiles/long roll and Japanese vertical punctuation/historical assets. APK gates inspect the actual ZIP contents, identity and signature. They do not exercise Android storage/share/lifecycle behaviour.

See the implementation report for executed results. No emulator or physical Android test was performed during this local hardening pass.

## Windows human acceptance — NOT EXECUTED

- [ ] Launch final installer on a clean supported Windows machine; verify unsigned warning or trusted production signature as appropriate.
- [ ] Choose a non-default installation folder; complete installation; launch installed app, desktop/start-menu shortcuts and icon; confirm About 0.7.0.
- [ ] Run portable EXE from a writable folder without installation. Check the visible window, resizing, input method, clipboard and normal close/relaunch.
- [ ] Open Chinese v1 and Japanese v2 projects; save/reopen and confirm transforms, variants and metadata. Test an existing v0.6 draft after backup.
- [ ] Confirm bundled Chinese fonts and all five Yuji variants, CODH inspector and offline licence text; test with network disabled.
- [ ] Export PNG, project JSON and historical long-roll ZIP to a chosen folder; inspect artwork and attribution/license manifests.
- [ ] Install/upgrade/uninstall on a disposable test profile; verify expected user-data preservation. Do not use the user's live installation for destructive checks.

Installer **payload** verification and unpacked/portable renderer automation do not count as installer wizard or visible desktop acceptance.

## Android physical-device acceptance — NOT EXECUTED — requires physical device

- [ ] Verify certificate/package/version with the script, install the exact APK and launch. Use the existing certificate for an in-place prior-version upgrade where compatible; otherwise back up/export before reinstalling.
- [ ] Confirm Chinese fonts, Yuji Syuku/Mai/Boku, Akari/Akebono hentaigana, repeated kana and CODH historical samples, including licence/DOI/source inspector.
- [ ] Compose mixed kanji/hiragana/katakana/punctuation horizontally and vertically. Check `「日本」、。ー` without claiming full kinsoku/connected kana support.
- [ ] Generate long rolls, browse pages and export a small and a large composition; observe memory, responsiveness and cancellation.
- [ ] Save/reload project; export PNG and ZIP; inspect provenance and share-alike files on another device/desktop.
- [ ] Test Android scoped-storage/save/share sheets, permission denial/retry and destination apps. Confirm no unnecessary storage permission prompts.
- [ ] Disable network, force-stop/relaunch and continue editing installed assets offline.
- [ ] Rotate, background/resume, handle keyboard and suspend/resume; verify no draft loss or blank glyphs.
- [ ] Test at least one low-memory supported device and current Android version; record actual devices and WebView versions. An emulator may supplement this checklist but must be labelled emulator-tested.

## Release decision

For v0.7.0, the release owner authorises unsigned Windows and offline Web publication with the unchecked native limitations disclosed. Android publication remains excluded pending production signing and physical-device acceptance. Clean tagged verification is still required. Known Japanese typesetting limitations are documented scope limits, not tasks to implement in this hardening pass. Five reviewed build-only dependency warnings remain visible and expire for re-review. Do not mark any unchecked native row passed.
