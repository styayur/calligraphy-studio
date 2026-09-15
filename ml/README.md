# ML extension boundary

Phase 2's baseline embedding is intentionally implemented in the API as `visual-geometry-256-v1` so it remains deterministic, dependency-light, and deployable without model weights.

This directory is reserved for model-backed replacements and generation work:

- `embeddings/`: learned glyph encoders, model cards, hashes, and preprocessing versions.
- `similarity/`: ANN indexes, evaluation sets, and retrieval benchmarks.
- `generation/`: structure-conditioned and style-reference-conditioned generation.

A learned encoder must be released under a new model name and remain compatible with the existing Glyph API. Phase 3 generation is still gated by source rights, provenance requirements, and explicit approval.
