from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.schemas import BatchComposeRequest, BatchComposeResponse, BatchPlacement, GlyphInstance, GlyphRead
from app.services.fallback_service import FallbackRequest, FallbackService
from app.services.glyph_service import GlyphService


@dataclass(slots=True)
class _Position:
    line: int
    column: int
    x: float
    y: float


class BatchComposeService:
    def __init__(self, glyph_service: GlyphService, fallback_service: FallbackService) -> None:
        self.glyph_service = glyph_service
        self.fallback_service = fallback_service

    def _lines(self, text: str) -> list[list[str]]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [[character for character in line if not character.isspace()] for line in normalized.split("\n")]
        return [line for line in lines if line] or [[character for character in normalized if not character.isspace()]]

    def _positions(self, request: BatchComposeRequest, lines: list[list[str]]) -> list[tuple[str, _Position]]:
        step_x = request.cell_width + request.gap_x
        step_y = request.cell_height + request.gap_y
        result: list[tuple[str, _Position]] = []

        if request.layout == "grid":
            flattened = [character for line in lines for character in line]
            for index, character in enumerate(flattened):
                row = index // request.columns
                column = index % request.columns
                result.append(
                    (
                        character,
                        _Position(
                            line=row,
                            column=column,
                            x=request.start_x + column * step_x + request.cell_width / 2,
                            y=request.start_y + row * step_y + request.cell_height / 2,
                        ),
                    )
                )
            return result

        if request.layout == "horizontal-ltr":
            for line_index, line in enumerate(lines):
                for column, character in enumerate(line):
                    result.append(
                        (
                            character,
                            _Position(
                                line=line_index,
                                column=column,
                                x=request.start_x + column * step_x + request.cell_width / 2,
                                y=request.start_y + line_index * step_y + request.cell_height / 2,
                            ),
                        )
                    )
            return result

        for line_index, line in enumerate(lines):
            for row, character in enumerate(line):
                result.append(
                    (
                        character,
                        _Position(
                            line=line_index,
                            column=row,
                            x=request.start_x - line_index * step_x + request.cell_width / 2,
                            y=request.start_y + row * step_y + request.cell_height / 2,
                        ),
                    )
                )
        return result

    def compose(self, session: Session, request: BatchComposeRequest) -> BatchComposeResponse:
        lines = self._lines(request.text)
        resolved_cache: dict[str, GlyphRead | None] = {}
        missing: list[str] = []
        placements: list[BatchPlacement] = []

        for character, position in self._positions(request, lines):
            if character not in resolved_cache:
                exact = self.glyph_service.list(
                    session,
                    character=character,
                    calligrapher=request.calligrapher,
                    style=request.style,
                    dataset=request.dataset,
                    limit=1,
                )
                glyph = exact.items[0] if exact.items else None
                if glyph is None and request.use_structural_fallback:
                    fallback = self.fallback_service.resolve(
                        session,
                        FallbackRequest(
                            character=character,
                            calligrapher=request.calligrapher,
                            style=request.style,
                            dataset=request.dataset,
                            use_structural_fallback=True,
                        ),
                    )
                    glyph = fallback.glyph if fallback.resolved else None
                resolved_cache[character] = glyph

            glyph = resolved_cache[character]
            if glyph is None:
                if character not in missing:
                    missing.append(character)
                continue

            scale = min(
                request.cell_width / glyph.asset.width,
                request.cell_height / glyph.asset.height,
            ) * 0.86
            instance = GlyphInstance(
                **{
                    **glyph.model_dump(),
                    "id": str(uuid4()),
                    "glyph_id": glyph.id,
                    "transform": {
                        **glyph.transform.model_dump(),
                        "x": position.x,
                        "y": position.y,
                        "scaleX": scale,
                        "scaleY": scale,
                    },
                }
            )
            placements.append(BatchPlacement(glyph=instance, line=position.line, column=position.column))

        total = sum(len(line) for line in lines)
        return BatchComposeResponse(
            placements=placements,
            missing=missing,
            total_characters=total,
            resolved_characters=len(placements),
        )
