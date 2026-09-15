# Third-party notices

## Hanzi Writer structural data

The fallback glyph generator uses character stroke data from:

- https://github.com/chanind/hanzi-writer-data
- Derived from Make Me A Hanzi and Arphic Technology fonts.

The data and any modified redistribution are governed by the ARPHIC PUBLIC LICENSE. The complete license text is included at `third_party/hanzi-writer/ARPHICPL.TXT`.

The generated SVG records a modification notice in its Glyph metadata and must keep the same license obligations when redistributed.

## NCCU Cursive Chinese Calligraphy Dataset

The bundled cursive Test subset is licensed under the MIT License. The complete license is included at `samples/cursive/raw/LICENSE`, and source paths are recorded in `samples/cursive/raw/metadata.json`.


## OFL calligraphy fonts

The bundled font files and their SIL Open Font License texts are located under `samples/fonts/`. Their font families are Ma Shan Zheng (楷书), Zhi Mang Xing (行书), and Liu Jian Mao Cao (草书). Each generated Glyph records the source font SHA-256 and OFL-1.1 metadata.

## Non-commercial fonts

No non-commercial font binaries are bundled. The manifest template `samples/fonts/noncommercial.example.json` is for user-provided local files whose license permits local use but may prohibit redistribution, derivatives, or commercial use.
