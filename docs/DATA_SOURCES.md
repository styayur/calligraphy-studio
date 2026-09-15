# Data Sources and License Audit

This file records what was actually integrated and why other links were not treated as importable data.

## Integrated

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
