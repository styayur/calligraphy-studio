# Phase Gates

## Phase 1 — completed

```text
MCCD/Cursive import
→ FastAPI Glyph API
→ React/Konva editor
→ JSON project
→ PNG export
```

Completed capabilities:

- Provider-based MCCD LMDB/manifest import and rights metadata.
- NCCU MIT cursive dataset import with actual sample assets.
- OFL-1.1 font import for 楷书、行书、草书 with font hash and license metadata.
- Generic font-manifest import supporting commercial and non-commercial local fonts.
- Search, metadata filters, drag/click composition, layers, transforms, opacity, Multiply.
- Undo/redo, project JSON round-trip, server save, PNG export.
- Batch text composition with grid, horizontal and vertical right-to-left layouts.

## Phase 1.5 — completed

Hanzi Writer / Make Me A Hanzi structural fallback:

- Fetches or caches stroke JSON by character.
- Converts structural stroke paths to an SVG asset.
- Imports the result into the Glyph Store with `provenance.type = "fallback"`.
- Never labels the result as a historical original.
- Preserves ARPHIC PUBLIC LICENSE notices in `third_party/hanzi-writer/`.

## Phase 2 — completed baseline

Implemented:

- `visual-geometry-256-v1`: deterministic 256-dimensional ink and edge geometry embedding.
- Embedding persistence with source checksum and model version.
- Reindex API and CLI.
- Cosine similarity API with same-style and same-dataset filters.
- Inspector UI showing similar glyphs from the same script style.
- Batch composer can use the store and structural fallback for missing characters.

This is intentionally a reproducible geometry baseline rather than a learned semantic style model. A learned encoder can replace it by adding a new model name while preserving the same Glyph Store and API contracts.

## Phase 3 — still gated

AI generation remains disabled. Before enabling it:

- The user must explicitly approve the generation phase.
- Reference rights must allow the intended derivative use.
- Generation must receive character structure plus style references, not only a raw style prompt.
- Every output must be marked `generated` with confidence and reference IDs.
- Human review must exist before generated characters are treated as publishable.
