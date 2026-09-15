# Font-backed glyph library

The bundled fonts are redistributable under the SIL Open Font License 1.1:

- Ma Shan Zheng — 楷书
- Zhi Mang Xing — 行书
- Liu Jian Mao Cao — 草书

`manifest.json` maps each font file to style, designer, source, license, rights, and target characters. `FontManifestProvider` renders covered characters to transparent PNG Glyphs and stores the font SHA-256 and license metadata.

Run:

```powershell
python scripts/fetch_open_fonts.py
python -m app.cli import-font-manifest --manifest samples/fonts/manifest.json
```

`noncommercial.example.json` is a template for local fonts whose licenses do not permit redistribution. Do not commit those font binaries unless their license allows it.
