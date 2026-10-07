# Font and Glyph License Guide

The importer does not infer legal permission from a license name. Every font entry must supply explicit `rights` fields.

## Supported license families

### SIL Open Font License 1.1 (OFL-1.1)

- Commercial documents using the font: normally allowed.
- Redistribution of font files or font-software derivatives: must follow OFL.
- Reserved font names: modified versions must follow the reserved-name rules.
- Documents created with the font are not required to be OFL.

Bundled examples: Ma Shan Zheng (楷书), Zhi Mang Xing (行书), Liu Jian Mao Cao (草书).

Also bundled: **Yuji Syuku / Mai / Boku / Akari / Akebono**, Version 3.002, Kinuta Font Factory / Yuji Kataoka, pinned commit `efec977b14b57c19eb85d468edcfbbad13139e67`. See [exact per-font checksums and attribution](../third_party/japanese/yuji/provenance.json), [original OFL text](../third_party/japanese/yuji/OFL.txt) and [font manifest](../samples/fonts/japanese/manifest.json). Runtime compressed TTFs decompress to the exact original binaries. No modified fonts are renamed or marketed as original manuscripts.

The current source build also bundles **Klee One Regular** (Fontworks / Klee Project, Version 1.000, pinned commit `8b0532731b63ad8a445ca341d8d7d941079b83ab`) as Japanese handwriting, and a 2.17 MB subset of **Source Han Serif JP Regular** (Adobe, upstream 2.003R, commit `7889f11bf31170b5d092a083b357c8c8130f89e0`) for coverage only. Both remain OFL 1.1. The modified subset has the internal family name `Calligraphy JP Coverage Serif` to respect Adobe's reserved font name `Source`. Original and derivative SHA-256 hashes, subset command and author records are in the [manifest](../samples/fonts/japanese/manifest.json); licence texts are [Klee](../third_party/japanese/klee/OFL.txt) and [Source Han Serif](../third_party/japanese/source-han-serif/OFL.txt). The coverage font is neither ordinary calligraphy nor a historical original. [Coverage benchmark](JAPANESE_COVERAGE.md).

Akari and Akebono historical kana outlines occupy modern hiragana codepoints. Their `hentaigana` visual variant and font ID remain distinct even though semantic text is identical; ordinary modern composition excludes them by default.

### CC BY-SA 4.0 historical images

CODH images are not font software. Original crop images and normalized ink masks retain CC BY-SA 4.0, attribution, DOI, modification notices and source checksum. Adapted artwork is exported with a machine-readable and human-readable attribution manifest plus complete licence. This does not impose CC BY-SA on the application's source code. [Historical provenance](../third_party/japanese/codh/provenance.json) and [licence](../third_party/japanese/codh/CC-BY-SA-4.0.txt) are independent from MIT and OFL.

### MIT

- Commercial use, modification, and redistribution are allowed with copyright/license notice.
- Used by the bundled NCCU cursive dataset subset.

### Apache License 2.0

- Commercial use and redistribution are allowed.
- Preserve notices and comply with patent/attribution terms.
- Supported by `FontManifestProvider`; no Apache font binary is bundled by default.

### GPL with font exception

- The exception matters. Without it, embedding a font into a document can create distribution obligations that many users do not expect.
- Store the exact font-exception text in the source record before enabling commercial use.
- Supported by the generic manifest, but not bundled.

### ARPHIC PUBLIC LICENSE

- Commercial use and redistribution are allowed under its terms.
- Modified font/data redistributions must remain freely available under the same license.
- Used by Hanzi Writer structural data.

### CC BY-NC 4.0 / CC BY-NC-ND 4.0

- Non-commercial use only.
- ND additionally forbids derivative works.
- MCCD is CC BY-NC-ND; HCSU data is CC BY-NC.
- The UI/source warnings retain NC/ND information, and future AI generation must reject references whose rights do not allow derivatives.

### User-provided proprietary or personal-use fonts

- Do not commit the font file when redistribution is forbidden.
- Keep only a local absolute path and exact license metadata in the manifest.
- Use `--commercial-only` to admit only entries with `commercial_use: true`; unknown is not permission.

## Required rights fields

```json
{
  "commercial_use": true,
  "derivatives_allowed": true,
  "redistribution_allowed": true,
  "research_use": true,
  "attribution_required": true,
  "font_license": true,
  "share_alike_required": false
}
```

Unknown values should be `null`, not optimistic booleans.
