from __future__ import annotations

import io
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
from PIL import Image, ImageOps
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.models import Glyph, GlyphEmbedding
from app.schemas import EmbeddingIndexResult, GlyphRead, SimilarGlyphItem, SimilarityResponse
from app.services.glyph_service import glyph_to_schema

MODEL_NAME = "visual-geometry-256-v1"
IMAGE_SIZE = 64
CELLS = 8
MAX_REMOTE_BYTES = 20 * 1024 * 1024


class VisualGlyphEmbedder:
    """Deterministic offline embedding based on multi-scale ink and edge geometry."""

    model_name = MODEL_NAME

    @staticmethod
    def _crop_ink(image: Image.Image) -> Image.Image:
        rgba = image.convert("RGBA")
        alpha = rgba.getchannel("A")
        if alpha.getextrema()[0] < 255:
            box = alpha.getbbox()
        else:
            grayscale = rgba.convert("L")
            ink = grayscale.point(lambda value: 255 if value < 245 else 0)
            box = ink.getbbox()
        return rgba.crop(box) if box else rgba

    @staticmethod
    def _normalize_polarity(image: Image.Image) -> Image.Image:
        grayscale = image.convert("L")
        width, height = grayscale.size
        border = 2
        corners = [
            grayscale.crop((0, 0, border, border)).resize((1, 1)).getpixel((0, 0)),
            grayscale.crop((max(0, width - border), 0, width, border)).resize((1, 1)).getpixel((0, 0)),
            grayscale.crop((0, max(0, height - border), border, height)).resize((1, 1)).getpixel((0, 0)),
            grayscale.crop((max(0, width - border), max(0, height - border), width, height)).resize((1, 1)).getpixel((0, 0)),
        ]
        if sum(corners) / len(corners) < 127:
            return ImageOps.invert(grayscale)
        return grayscale

    @classmethod
    def embed_image(cls, image: Image.Image) -> np.ndarray:
        cropped = cls._crop_ink(image)
        normalized = cls._normalize_polarity(cropped)
        side = max(normalized.width, normalized.height, 1)
        square = Image.new("L", (side, side), 255)
        square.paste(normalized, ((side - normalized.width) // 2, (side - normalized.height) // 2))
        resized = square.resize((IMAGE_SIZE, IMAGE_SIZE), Image.Resampling.LANCZOS)
        ink = 1.0 - np.asarray(resized, dtype=np.float32) / 255.0
        gradient_y, gradient_x = np.gradient(ink)
        cell_size = IMAGE_SIZE // CELLS
        features: list[float] = []
        for row in range(CELLS):
            for column in range(CELLS):
                y0 = row * cell_size
                x0 = column * cell_size
                cell = ink[y0 : y0 + cell_size, x0 : x0 + cell_size]
                features.extend(
                    [
                        float(cell.mean()),
                        float(cell.std()),
                        float(np.abs(gradient_x[y0 : y0 + cell_size, x0 : x0 + cell_size]).mean()),
                        float(np.abs(gradient_y[y0 : y0 + cell_size, x0 : x0 + cell_size]).mean()),
                    ]
                )
        vector = np.asarray(features, dtype=np.float32)
        norm = float(np.linalg.norm(vector))
        if norm <= 1e-8:
            vector = np.zeros_like(vector)
        else:
            vector /= norm
        return vector


class EmbeddingService:
    def __init__(self, assets_dir: str | Path, fetch_remote: bool = True) -> None:
        self.assets_dir = Path(assets_dir).resolve()
        self.fetch_remote = fetch_remote

    def _asset_bytes(self, glyph: Glyph) -> bytes:
        if glyph.asset_url.startswith("/assets/"):
            relative = glyph.asset_url.removeprefix("/assets/")
            path = (self.assets_dir / relative).resolve()
            if self.assets_dir not in path.parents:
                raise ValueError("Asset path escapes the configured storage root")
            return path.read_bytes()
        if glyph.asset_url.startswith(("http://", "https://")):
            if not self.fetch_remote:
                raise ValueError("Remote assets are disabled for embedding")
            request = Request(glyph.asset_url, headers={"User-Agent": "CalligraphyStudio/0.2"})
            with urlopen(request, timeout=20) as response:  # noqa: S310
                data = response.read(MAX_REMOTE_BYTES + 1)
            if len(data) > MAX_REMOTE_BYTES:
                raise ValueError("Remote asset exceeds 20 MB embedding limit")
            return data
        raise ValueError(f"Unsupported asset URL for embedding: {glyph.asset_url}")

    def embed_glyph(self, glyph: Glyph) -> np.ndarray:
        with Image.open(io.BytesIO(self._asset_bytes(glyph))) as image:
            return VisualGlyphEmbedder.embed_image(ImageOps.exif_transpose(image))

    def ensure_embedding(self, session: Session, glyph: Glyph) -> GlyphEmbedding:
        existing = session.scalar(
            select(GlyphEmbedding).where(
                GlyphEmbedding.glyph_id == glyph.id,
                GlyphEmbedding.model_name == MODEL_NAME,
            )
        )
        if existing and existing.source_checksum == glyph.checksum:
            return existing
        vector = self.embed_glyph(glyph)
        if existing is None:
            existing = GlyphEmbedding(
                glyph_id=glyph.id,
                model_name=MODEL_NAME,
                dimension=int(vector.shape[0]),
                vector=vector.astype("<f4", copy=False).tobytes(),
                norm=float(np.linalg.norm(vector)),
                source_checksum=glyph.checksum,
            )
            session.add(existing)
        else:
            existing.dimension = int(vector.shape[0])
            existing.vector = vector.astype("<f4", copy=False).tobytes()
            existing.norm = float(np.linalg.norm(vector))
            existing.source_checksum = glyph.checksum
        session.flush()
        return existing

    def index(
        self,
        session: Session,
        *,
        characters: set[str] | None = None,
        limit: int | None = None,
        force: bool = False,
    ) -> EmbeddingIndexResult:
        statement = select(Glyph).options(selectinload(Glyph.source)).order_by(Glyph.created_at)
        if characters:
            statement = statement.where(Glyph.character.in_(characters))
        if limit:
            statement = statement.limit(limit)
        glyphs = list(session.scalars(statement).all())
        indexed = skipped = failed = 0
        errors: list[str] = []
        for glyph in glyphs:
            try:
                if not force:
                    existing = session.scalar(
                        select(GlyphEmbedding).where(
                            GlyphEmbedding.glyph_id == glyph.id,
                            GlyphEmbedding.model_name == MODEL_NAME,
                            GlyphEmbedding.source_checksum == glyph.checksum,
                        )
                    )
                    if existing:
                        skipped += 1
                        continue
                self.ensure_embedding(session, glyph)
                indexed += 1
            except Exception as exc:
                failed += 1
                if len(errors) < 50:
                    errors.append(f"{glyph.character} ({glyph.id}): {exc}")
        return EmbeddingIndexResult(
            model_name=MODEL_NAME,
            indexed=indexed,
            skipped=skipped,
            failed=failed,
            errors=errors,
        )

    def similar(
        self,
        session: Session,
        *,
        glyph_id: str,
        limit: int = 20,
        same_style: bool = False,
        same_dataset: bool = False,
    ) -> SimilarityResponse:
        target = session.scalar(
            select(Glyph)
            .options(selectinload(Glyph.source))
            .where(Glyph.id == glyph_id)
        )
        if target is None:
            raise KeyError("Glyph not found")
        target_embedding = self.ensure_embedding(session, target)

        statement = (
            select(GlyphEmbedding, Glyph)
            .join(Glyph, Glyph.id == GlyphEmbedding.glyph_id)
            .options(
                selectinload(Glyph.source),
                selectinload(Glyph.calligrapher),
                selectinload(Glyph.style),
                selectinload(Glyph.dynasty),
            )
            .where(
                GlyphEmbedding.model_name == MODEL_NAME,
                GlyphEmbedding.glyph_id != target.id,
            )
        )
        if same_style and target.style_id is not None:
            statement = statement.where(Glyph.style_id == target.style_id)
        if same_dataset:
            statement = statement.where(Glyph.source_id == target.source_id)
        rows = session.execute(statement).all()
        if not rows:
            return SimilarityResponse(target_id=target.id, model_name=MODEL_NAME, items=[])

        matrix = np.vstack(
            [np.frombuffer(row[0].vector, dtype="<f4").astype(np.float32) for row in rows]
        )
        target_vector = np.frombuffer(target_embedding.vector, dtype="<f4").astype(np.float32)
        scores = matrix @ target_vector
        count = min(limit, len(rows))
        best = np.argpartition(scores, -count)[-count:]
        best = best[np.argsort(scores[best])[::-1]]
        items = [
            SimilarGlyphItem(glyph=glyph_to_schema(rows[index][1]), score=float(scores[index]))
            for index in best
        ]
        return SimilarityResponse(target_id=target.id, model_name=MODEL_NAME, items=items)
