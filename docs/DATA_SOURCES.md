# Data Sources and License Audit

This file records what was actually integrated and why other links were not treated as importable data.

## Integrated

### Yuji Japanese font pack

Official source: [Kinutafontfactory/Yuji](https://github.com/Kinutafontfactory/Yuji), commit `efec977b14b57c19eb85d468edcfbbad13139e67`; all five files report **Version 3.002**. Yuji Syuku, Mai, Boku cover kanji/hiragana/katakana and punctuation; Akari/Akebono provide historical kana font alternates in modern hiragana slots. Designer: Yuji Kataoka / Kinuta Font Factory. License: OFL-1.1. Exact paths, authorship, checksums, copyright, original OFL text and source URLs are in `third_party/japanese/yuji/provenance.json` and `samples/fonts/japanese/manifest.json`. All glyphs have `font` provenance. These fonts are not historical originals.

Reproduce source files with `python scripts/fetch_japanese_fonts.py`, then `python scripts/build_browser_fonts.py`. Each download is pinned to the reviewed commit and checksum; no upstream scripts run. Browser compressed fonts retain exact original font bytes; all platforms ship the same manifest and independently visible licences.

### CODH Japanese historical sample

Authoritative resource: [CODH / ROIS character shapes](https://codh.rois.ac.jp/char-shape/), **v2, 2019-11-11**, DOI [10.20676/00000340](https://doi.org/10.20676/00000340). Source attribution: 日本古典籍くずし字データセット (国文研所蔵／CODH加工). CC BY-SA 4.0; not MIT. Dataset transcriptions can merge kyūjitai with modern kanji and hentaigana with modern hiragana. Preserve source transcriptions and occurrence identity rather than claiming unique historical semantic mappings.

Bundled subset: 20 upstream display crops from book `200006663` (ぢぐち), selected from official [v2 archive](https://codh.rois.ac.jp/char-shape/dataset/v2/200006663.zip). Archive SHA-256: `3e47c4f1f4b12dec83732dad8e398780851751bd225114395d420857d2bb3671`. The original archive is roughly 7.71 MB; full upstream dataset ZIP is roughly 7.35 GB, which is unsuitable for platform packaging. [Provenance receipt](../third_party/japanese/codh/provenance.json) and [sample manifest](../samples/japanese/historical/sample/manifest.json) retain each original checksum, book/page/bbox, source URI and Unicode mapping. Period, language and calligrapher are unknown. Writing tradition identifies the Japanese collection, not necessarily the language of every text.

`python scripts/build_japanese_sample.py` reproducibly generates transparent masks with explicit processing notices and CC-BY-SA-4.0 derivative licence. Artwork exports containing adapted CODH glyphs include JSON/TXT attribution and complete licence; share-alike obligations stay attached. No KMNIST, Kuzushiji-49, Kuzushiji-Kanji, Kaggle mirrors or unofficial reuploads are bundled.

### Japanese historical corpus installation

Normal offline editing requires no corpus download. Optional corpus imports need the existing local Python API; standalone web/APK/desktop core packs include only fonts and the small sample.

```sh
pip install -r apps/api/requirements.txt
python scripts/import_codh.py --url https://codh.rois.ac.jp/char-shape/dataset/v2/200006663.zip --sha256 3e47c4f1f4b12dec83732dad8e398780851751bd225114395d420857d2bb3671 --book-id 200006663 --work ぢぐち
```

For another official v2 book/archive, supply its independently reviewed SHA-256. Do not reuse the sample checksum or invent an upstream release checksum. For fully offline import, create a schema-2 receipt next to downloaded archives and use `--manifest data/imports/receipt.json`:

```json
{"schema_version":2,"dataset_version":"v2","archives":[{"file":"200006663.zip","sha256":"3e47c4f1f4b12dec83732dad8e398780851751bd225114395d420857d2bb3671","books":{"200006663":{"work":"ぢぐち"}}}]}
```

Use `--characters あい国` / `--limit 100` for a small local corpus; `--db-url` / `--assets-dir` override destinations. Ctrl+C leaves committed checkpoints; repeating the same command skips existing identity/source/checksum records. Downloads restart after interruption; import is repeatable, not a byte-range resumable downloader. Archives are streamed in place and never extracted. No network is needed after assets are installed; API lists are indexed/paginated and images remain lazy.

Raw archives/receipts live under ignored `data/imports/`; runtime images under ignored `storage/assets/`. Historical original crops are `original` source records; any mask/composition records its changes. Never assign source period or calligrapher without evidence.

### NCCU Cursive Chinese Calligraphy Dataset

- Repository: https://github.com/nccuviplab/CursiveChineseCalligraphyDataset
- Source license: MIT
- Upstream description: 5,301 cursive character categories after removing numeric directory suffixes; 96×96 grayscale images; Training / Validation / Test splits.
- Attribution: VIPLab, Department of Computer Science, National Chengchi University, Taipei. The upstream README states that images were reorganized and redistributed with permission from the administrator of https://shufa.supfree.net/.
- Integration: `NCCUCursiveProvider`, CLI import command, and a 30-image Test subset in `samples/cursive/raw`.
- Rights metadata: commercial use, derivatives, redistribution, and research use are marked allowed with attribution required.

The upstream repository is about 1.4 GB. This project bundles only a small Test subset so the application can run immediately; use the import CLI for the authorized full checkout.

### Google Fonts OFL Calligraphy Fonts

- Sources:
  - https://github.com/googlefonts/mashanzheng
  - https://github.com/m4rc1e/zhimangxing
  - https://github.com/googlefonts/liujianmaocao
- Font families:
  - Ma Shan Zheng: brush-style 楷书
  - Zhi Mang Xing: 行书
  - Liu Jian Mao Cao: 草书
- License: SIL Open Font License 1.1
- Integration: `FontManifestProvider` converts covered characters into transparent 768×768 PNG Glyphs.
- Bundled files: TTF and the corresponding OFL text are stored in `samples/fonts/`.
- Rights metadata: commercial use, derivatives and redistribution are marked allowed, with attribution and the font-license obligations preserved.
- Provenance: these are labeled `font`, not historical originals and not AI output.

The OFL permits fonts to be used in documents without imposing OFL on the document. Distribution of modified font software or font derivatives still requires compliance with OFL terms, including reserved-name rules where applicable.

### User-provided non-commercial fonts

Non-commercial fonts are supported through the same manifest provider but are not bundled or downloaded unless their license explicitly permits redistribution.

Use `samples/fonts/noncommercial.example.json` as a template. The provider preserves fields such as:

- `commercial_use: false`
- `derivatives_allowed: false`
- `redistribution_allowed: false`
- `research_use: true`

`import-font-manifest --commercial-only` excludes entries whose license disallows commercial use. The UI displays an authorization warning for NC/ND sources. Because the source font is not redistributed, only the user-provided local path and metadata are stored in the manifest.

### Hanzi Writer Structural Data

- Repository: https://github.com/chanind/hanzi-writer-data
- Source project: Make Me A Hanzi / Arphic fonts
- Data license: ARPHIC PUBLIC LICENSE
- Integration: optional structure fallback that converts stroke paths into an SVG glyph marked `fallback`.
- License copy: `third_party/hanzi-writer/ARPHICPL.TXT`.
- Rights metadata: commercial use and redistribution are allowed by the license, but modified font/data redistributions must remain freely available under the same license and retain notices. Verify the exact obligations before distributing generated derivatives.

Hanzi Writer is not classified as AI and is never labeled as a historical original.

### MCCD

- Repository: https://github.com/SCUT-DLVCLab/MCCD
- Data license: CC BY-NC-ND 4.0, non-commercial research only.
- Integration: LMDB and manifest import providers only. No MCCD images are bundled in this repository.
- Consequences: the built-in rights record forbids commercial use and derivative generation by default.

## Reviewed but not imported

### chenjiandongx/calligraphy and R3333333/Calligraphy-Dataset

The URLs supplied in the original brief returned HTTP 404 during the audit. No repository, release, license, or stable data format could be verified, so no code or images were imported from them.

### cnex.org.tw

At audit time this domain resolved to the CNEX documentary foundation, not the Taiwanese full-character library. The likely intended official source is CNS 11643 / 全字庫:

- https://www.cns11643.gov.tw/

It is a standards glyph resource, not specifically a cursive calligraphy corpus. Any font or glyph import should be implemented as a separate font-backed provider after checking the current Open Government Data terms.

### Kouzan Brush Font

- https://kouzan.info/
- The site did not provide a TLS connection during this audit, and no clear redistribution or commercial-use grant was verified.
- Kouzan is therefore treated as a user-supplied licensed font source, not bundled data.

### HCSU

- Repository: https://github.com/209-Tongji/HCSU
- Data license: CC BY-NC 4.0.
- Suitable for non-commercial research experiments, but not bundled or enabled for unrestricted product use without separate permission.

### BCSS

The public repository currently documents that the dataset will be released in the future and does not contain the image corpus. No dataset images were imported.
