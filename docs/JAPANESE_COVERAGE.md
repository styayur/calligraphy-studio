# Japanese coverage benchmark

This measures Unicode codepoint coverage in bundled Japanese fonts; it does not assess visual quality,
regional glyph accuracy per character, or complete Japanese typography. The fallback is a renamed,
OFL-licensed subset derived from Source Han Serif JP, and is never labelled a manuscript.

The Jōyō 2010, Jinmeiyō, JIS X 0208 kanji and JIS X 0213 kanji sets come from
[Unicode Unihan 16.0.0](https://www.unicode.org/Public/16.0.0/ucd/Unihan.zip)
(`SHA-256 b8f000df69de7828d21326a2ffea462b04bc7560022989f7cc704f10521ef3e0`). The JIS properties count ideographs only;
they do not cover each standard's punctuation, kana or multi-codepoint sequences.
JIS X 0213 here is the union of Unihan `kJis0` and `kJIS0213`, including its JIS X 0208 base.
The reviewed project corpus is a separately labelled fixture from the existing Japanese examples
and selected uncommon characters. Jinmeiyō includes Unihan-marked variants.

| Repertoire | Total | Yuji | Klee One | Coverage fallback | Combined | Remaining missing |
| --- | ---: | ---: | ---: | ---: | ---: | --- |
| Jōyō 2010 | 2136 | 2136 | 2136 | 0 | 2136 | None |
| Jinmeiyō 2010 | 863 | 863 | 860 | 0 | 863 | None |
| JIS X 0208 kanji | 6356 | 6356 | 6356 | 0 | 6356 | None |
| JIS X 0213 kanji | 10051 | 6745 | 7680 | 2359 | 10051 | None |
| Reviewed project corpus | 46 | 45 | 46 | 0 | 46 | None |

The fallback intentionally contains only characters absent from both Yuji and Klee in the
pinned target sets. Its standalone column is therefore small by design. Ordinary composition
prefers Yuji and Klee; strict Japanese mode can use the fallback without Chinese substitution.

The two new compressed runtime fonts add 6,578,155 bytes (Klee 4,746,784; coverage subset 1,831,371).
The source OTF is 24,574,024 bytes and is not bundled in platform packages.

Reproduce from pinned upstream binaries and Unihan data:

```sh
python scripts/build_japanese_coverage.py --fetch
python scripts/build_browser_fonts.py
python scripts/report_japanese_coverage.py --write
```

The font build script verifies original SHA-256 hashes, preserves HarfBuzz layout features,
renames the derivative's reserved font family, and checks its SHA-256 against the pinned font manifest.
The JSON report beside this file contains exact per-font checksums and all remaining missing characters.
