from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from sqlalchemy.orm import Session

from app.providers.hanzi_writer import HANZI_DATASET, HanziWriterProvider
from app.schemas import GlyphRead
from app.services.glyph_importer import GlyphImporter
from app.services.glyph_service import GlyphService


@dataclass(slots=True)
class FallbackRequest:
    character: str
    calligrapher: str | None = None
    style: str | None = None
    dataset: str | None = None
    references: list[str] = field(default_factory=list)
    use_structural_fallback: bool = True


@dataclass(slots=True)
class FallbackResult:
    level: int
    resolved: bool
    glyph: GlyphRead | None = None
    references: list[str] = field(default_factory=list)
    reason: str | None = None


class SimilarityProvider(Protocol):
    def find_style_references(self, request: FallbackRequest) -> list[str]: ...


class StructuralProvider(Protocol):
    def render_structure(self, character: str) -> str: ...


class GenerationProvider(Protocol):
    def generate(self, request: FallbackRequest) -> GlyphRead: ...


class FallbackService:
    """Real glyph -> style references -> structural fallback; generation remains gated."""

    def __init__(
        self,
        glyph_service: GlyphService,
        *,
        glyph_importer: GlyphImporter | None = None,
        hanzi_cache_dir: str | Path | None = None,
        fetch_remote_hanzi: bool = True,
    ) -> None:
        self.glyph_service = glyph_service
        self.glyph_importer = glyph_importer
        self.hanzi_cache_dir = Path(hanzi_cache_dir) if hanzi_cache_dir else None
        self.fetch_remote_hanzi = fetch_remote_hanzi

    def _style_references(
        self,
        session: Session,
        request: FallbackRequest,
    ) -> list[str]:
        if not request.calligrapher and not request.style:
            return []
        samples = self.glyph_service.list(
            session,
            calligrapher=request.calligrapher,
            style=request.style,
            limit=8,
        )
        return [item.id for item in samples.items]

    def _structural_fallback(
        self,
        session: Session,
        request: FallbackRequest,
    ) -> GlyphRead | None:
        if not request.use_structural_fallback or self.glyph_importer is None or self.hanzi_cache_dir is None:
            return None
        provider = HanziWriterProvider(
            request.character,
            cache_dir=self.hanzi_cache_dir,
            fetch_remote=self.fetch_remote_hanzi,
        )
        result = self.glyph_importer.import_provider(provider)
        if result.imported == 0 and result.failed:
            return None
        candidates = self.glyph_service.list(
            session,
            character=request.character,
            limit=5,
        )
        return next(
            (
                item
                for item in candidates.items
                if item.source.dataset == HANZI_DATASET
                and item.provenance.type == "fallback"
            ),
            None,
        )

    def resolve(self, session: Session, request: FallbackRequest) -> FallbackResult:
        exact = self.glyph_service.list(
            session,
            character=request.character,
            calligrapher=request.calligrapher,
            style=request.style,
            limit=1,
        )
        if exact.items:
            return FallbackResult(level=1, resolved=True, glyph=exact.items[0])

        references = self._style_references(session, request)
        structural = self._structural_fallback(session, request)
        if structural is not None:
            return FallbackResult(
                level=3,
                resolved=True,
                glyph=structural,
                references=references,
                reason="No original glyph matched; generated a structural fallback.",
            )
        if references:
            return FallbackResult(
                level=2,
                resolved=False,
                references=references,
                reason="Style references found, but AI synthesis is not enabled.",
            )
        return FallbackResult(
            level=3,
            resolved=False,
            reason="Structural fallback is unavailable for this character.",
        )
