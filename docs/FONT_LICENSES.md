# Font and Glyph License Guide

The importer does not infer legal permission from a license name. Every font entry must supply explicit `rights` fields.

## Supported license families

### SIL Open Font License 1.1 (OFL-1.1)

- Commercial documents using the font: normally allowed.
- Redistribution of font files or font-software derivatives: must follow OFL.
- Reserved font names: modified versions must follow the reserved-name rules.
- Documents created with the font are not required to be OFL.

Bundled examples: Ma Shan Zheng (楷书), Zhi Mang Xing (行书), Liu Jian Mao Cao (草书).

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
- Use `--commercial-only` to exclude entries with `commercial_use: false`.

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
