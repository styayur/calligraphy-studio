from __future__ import annotations

import re
import unicodedata
from pathlib import Path


def slugify(value: str, fallback: str = "item") -> str:
    normalized = unicodedata.normalize("NFKC", value).strip().lower()
    normalized = re.sub(r"[^\w\u3400-\u9fff-]+", "-", normalized, flags=re.UNICODE)
    normalized = re.sub(r"-{2,}", "-", normalized).strip("-")
    return normalized or fallback


def safe_filename(value: str, fallback: str = "glyph") -> str:
    cleaned = unicodedata.normalize("NFKC", value)
    cleaned = re.sub(r'[<>:"/\\|?*\x00-\x1f]+', "-", cleaned).strip(" .-")
    return cleaned[:80] or fallback


def ensure_within(root: Path, target: Path) -> Path:
    resolved_root = root.resolve()
    resolved_target = target.resolve()
    if resolved_root != resolved_target and resolved_root not in resolved_target.parents:
        raise ValueError(f"Path escapes configured root: {target}")
    return resolved_target