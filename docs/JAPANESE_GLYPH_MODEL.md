# Japanese glyph model

Japanese is the first expansion beyond Chinese; this is an East Asian workbench foundation, not a complete catalogue of Japanese calligraphy.

## Semantic text and visual identity

`Glyph.character` remains convenient plain text. `identity` carries exact text, Unicode codepoints, script, language, locale and optional canonical relationship. `variant` separately carries type, stable ID, font glyph ID and glyph name. A decomposed dakuten sequence or supplementary character remains one grapheme in composition. Unknown cultural facts remain null; Unicode script detection is not language identification.

Database uniqueness uses a digest of semantic text, locale/language/script, tradition and visual variant together with source and image checksum. Multiple outlines or historical occurrences of the same codepoint coexist, including identical images with distinct regional identities. A project instance still references its source `glyph_id` and owns its own transform.

## 新字体 / Shinjitai and 旧字体 / Kyūjitai

Modern Japanese forms and older forms may have different Unicode characters. A small reviewed table identifies 国／國、学／學、体／體、旧／舊、広／廣; it records relationships without substituting text. It is not a complete orthography dictionary. Other forms stay `modern`/`regional` unless the provider supplies an explicit classification. Chinese simplified/traditional relationships and Japanese shinjitai/kyūjitai relationships are not interchangeable.

## 変体仮名 / Hentaigana

Some historical kana have dedicated Unicode characters; others are font alternates or source-specific transcriptions. Yuji Akari/Akebono render historical kana in modern hiragana slots. Preserve the typed hiragana as semantic text and label the outline `hentaigana` with its specific font variant ID. Never invent a one-to-one historical semantic mapping. Non-kana glyphs in these fonts are tagged font-alternate, not hentaigana. Strict modern mode excludes these fonts unless explicitly requested; related mode allows exploration within the selected tradition.

## くずし字 / Kuzushiji

Kuzushiji describes historical cursive forms, not a Unicode script or font family. CODH v2 crops are historical source occurrences with book/page/bounding-box IDs. CODH transcriptions can fold older kanji or kana into modern codepoints; that mapping does not recover the original semantic distinction. Record upstream mapping and source occurrence, leave unavailable period/author/language unknown. The bundled sample is 20 crops from ぢぐち, not a representative corpus of all Japanese calligraphy. ML benchmark images are not the production display library.

## Shared Han and regional forms

The same Han codepoint (for example 骨 or 辻) can have different Chinese and Japanese outlines. Locale, tradition and source are policy boundaries. Strict tradition filters incompatible/unknown traditions; related variants remain within tradition. Cross-tradition exploration is explicit and retains compatibility penalties. Existing Chinese fonts have known Chinese tradition but unverified locale; they are not falsely labeled zh-Hans or zh-Hant. Their repertoire includes simplified/traditional characters, with no complete automatic orthography conversion.

## OpenType shaping

Japanese path: exact Unicode sequence → script/language → HarfBuzz `locl` and optionally `vert`/`vrt2` → glyph IDs/names/positions → raster asset. Python uses uharfbuzz + FreeType; offline web/Windows/Android uses local HarfBuzz WASM and canvas outline rasterization. Record features, locale, script, glyph IDs/names, source font checksum and output checksum. Chinese legacy Pillow/canvas rendering remains to preserve existing output and is explicitly marked as not locale-aware shaping.

Yuji remains the primary modern Japanese calligraphy source. Klee One adds independent handwriting candidates. A renamed, OFL-licensed Source Han Serif JP subset covers the reviewed characters missing from both; its `coverage-fallback` role ranks below those visual sources and is still Japanese / `ja-JP` in strict mode. CODH historical crops remain a separate `original` source category. [Pinned coverage results and reproduction](JAPANESE_COVERAGE.md).

Rasterization is repeatable within each tested engine; Canvas and FreeType antialiasing are not promised to be byte-identical across platforms. Glyph-cell layout supports mixed kanji/kana, Japanese punctuation anchoring and font vertical alternates. Connected kana across cells, kinsoku line breaking, tate-chū-yoko, complete UAX #50 mixed Latin orientation and arbitrary IVS coverage are not implemented. Unsupported glyphs remain missing; do not synthesize an allegedly authentic shape.

## Provenance and rights

Keep `original`, `font`, `fallback`, `generated`. A normalized historical crop still derives from an `original` source; asset processing and derivative licence identify changes. Yuji always has `font` provenance. Every selected glyph retains source licence, rights, attribution, source URI and checksums. Visual Profile/harmony scores are computational signals, never authenticity or objective aesthetic judgements.

Authoritative references: [Yuji](https://github.com/Kinutafontfactory/Yuji), [CODH](https://codh.rois.ac.jp/char-shape/), [Japanese character policy](https://www.bunka.go.jp/kokugo_nihongo/sisaku/joho/joho/kijun/naikaku/kanji/), [Unicode vertical orientation](https://www.unicode.org/reports/tr50/), [HarfBuzz](https://harfbuzz.github.io/).
