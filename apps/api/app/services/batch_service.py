from __future__ import annotations

from dataclasses import dataclass
from uuid import uuid4

from sqlalchemy.orm import Session

from app.schemas import BatchComposeRequest, BatchComposeResponse, BatchPlacement, GlyphInstance, GlyphRead
from app.services.fallback_service import FallbackRequest, FallbackService
from app.services.glyph_service import GlyphService
from app.domain import require_rights
from app.services.asset_store import AssetStore
import regex


@dataclass(slots=True)
class _Position:
    line: int
    column: int
    x: float
    y: float


class BatchComposeService:
    def __init__(self, glyph_service: GlyphService, fallback_service: FallbackService, asset_store: AssetStore | None = None) -> None:
        self.glyph_service = glyph_service
        self.fallback_service = fallback_service
        self.asset_store = asset_store

    def _lines(self, text: str) -> list[list[str]]:
        normalized = text.replace("\r\n", "\n").replace("\r", "\n")
        lines = [[character for character in regex.findall(r"\X", line) if not character.isspace()] for line in normalized.split("\n")]
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
        if request.writing_tradition == "Japanese" and self.asset_store and request.dataset in (None, "Yuji Japanese Fonts"):
            from app.config import PROJECT_ROOT
            from app.providers.font_manifest import FontManifestProvider
            characters = {c for line in lines for c in line}
            missing_font_text = {c for c in characters if not self.glyph_service.list(session, character=c, writing_tradition='Japanese', provenance_type='font', limit=1).items}
            if missing_font_text:
                # Release the read transaction before the importer opens its write session.
                records = FontManifestProvider(PROJECT_ROOT / 'samples/fonts/japanese/manifest.json', characters=missing_font_text)
                importer = self.fallback_service.glyph_importer
                if importer:
                    session.commit()
                    importer.import_provider(records)
        resolved_cache: dict[str, GlyphRead | None] = {}
        vertical_shapers = {}
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
                    writing_tradition=request.writing_tradition, locale=request.locale,
                    script=request.script, variant_type=request.variant_type, mode=request.mode,
                    commercial_only=request.commercial_only,
                    limit=1,
                )
                glyph = exact.items[0] if exact.items else None
                if glyph is None and request.use_structural_fallback and request.writing_tradition != "Japanese":
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
            require_rights(glyph.source.rights, commercial=request.commercial_only,
                           derivative=glyph.provenance.type == "original" and glyph.source.rights.get("derivatives_allowed") is False)
            if (request.layout == "vertical-rtl" and glyph.provenance.type == "font" and glyph.source.language == "ja"
                    and glyph.metadata.get("shaping", {}).get("direction") != "ttb"):
                # Resolve font by its manifest ID, never trust an imported project filesystem path.
                from app.config import PROJECT_ROOT
                from app.services.font_shaper import FontShaper
                from app.services.asset_store import AssetStore
                from app.providers.base import RawGlyphRecord
                import json
                manifest_path = PROJECT_ROOT / "samples/fonts/japanese/manifest.json"
                entries = json.loads(manifest_path.read_text(encoding="utf-8"))["fonts"]
                entry = next((e for e in entries if e["id"] == glyph.metadata.get("font_id")), None)
                if entry:
                    if entry['id'] not in vertical_shapers:
                        vertical_shapers[entry['id']] = FontShaper(manifest_path.parent / entry["path"])
                    shaper = vertical_shapers[entry['id']]
                    if shaper.checksum != entry["sha256"]:
                        raise ValueError("Vertical source font checksum mismatch")
                    rendered = shaper.render(character, locale=entry["locale"], script=glyph.source.script, vertical=True)
                    if rendered:
                        if self.asset_store is None:
                            raise ValueError("Vertical font rendering requires the application's asset store")
                        stored = self.asset_store.persist(RawGlyphRecord(character=character,dataset=entry["dataset"],asset_bytes=rendered[0],original_filename=f"{entry['id']}-vertical.png"))
                        glyph = glyph.model_copy(deep=True)
                        glyph.asset.url, glyph.asset.checksum = stored.url, stored.checksum
                        glyph.asset.width, glyph.asset.height, glyph.asset.bbox = stored.width, stored.height, stored.bbox
                        glyph.metadata["shaping"] = rendered[1]
                        glyph.variant.id = (glyph.variant.id or glyph.id) + ":vertical"
                        glyph.variant.font_glyph_id = rendered[1]["font_glyph_ids"][0]
                        glyph.variant.glyph_name = rendered[1]["glyph_names"][0]
                        resolved_cache[character] = glyph

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
