# MCCD Import

## Official facts used by this code

MCCD's public repository documents:

- approximately 330,000 isolated calligraphic character images
- 7,765 character categories
- 10 script styles
- 15 dynasties
- 142 calligraphers
- PNG and LMDB release formats
- CC BY-NC-ND 4.0, non-commercial research only

The repository's data loader reads:

```text
num-samples
image-000000001
label-000000001
char-000000001
style-000000001
dynasty-000000001
```

Some archives may not include a literal `calligrapher-*` key; this importer treats `label-*` as the calligrapher index in `four-task` mode, matching the public loader's separate `label` and `char` fields. Use `inspect-lmdb` to verify the exact archive before a full import.

## Attribute maps

The archive may contain integer indices. Supply a JSON map:

```json
{
  "character": { "0": "一", "1": "丁" },
  "calligrapher": { "0": "王羲之", "1": "颜真卿" },
  "style": { "0": "篆书", "1": "隶书" },
  "dynasty": { "0": "先秦", "1": "汉" }
}
```

Values that are already Chinese strings pass through unchanged.

## Modes

- `four-task`: character + style + dynasty + calligrapher
- `character`: character-only LMDB
- `style`: style-only LMDB
- `dynasty`: dynasty-only LMDB
- `calligrapher`: calligrapher-only LMDB

Single-attribute subsets should normally be used for data validation. Importing every subset as separate glyphs can duplicate images.

## Manifest mode

`MCCDManifestProvider` accepts CSV, JSON, or JSONL. Recommended columns:

```csv
character,asset,calligrapher,style,dynasty,work,bbox,width,height,license
山,images/shan.png,王羲之,行书,东晋,兰亭集序,"12,18,486,502",512,512,CC BY-NC-ND 4.0
```

Relative assets resolve against `--dataset-root`. Remote URLs are metadata-only unless `--download-remote` is supplied; in that case the asset is copied into local storage.

## Scale guidance

- Start with `--characters 山水雲龍` or `--limit 1000`.
- Run one small import and inspect the returned Glyph API records.
- Full LMDB import copies assets into object storage. Budget disk space before running it.
- Use WAL and a local SSD for SQLite during large imports.
- Keep raw MCCD data outside this repository.

## License gate

The CLI requires `--rights-confirmed`. This is not a legal conclusion; it is a guardrail that forces an explicit review. In particular, CC BY-NC-ND is incompatible with unrestricted commercial products and, depending on jurisdiction and use, may restrict generated derivatives.
