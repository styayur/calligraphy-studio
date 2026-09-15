from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GlyphSourceSchema(BaseModel):
    dataset: str
    calligrapher: str | None = None
    style: str | None = None
    dynasty: str | None = None
    work: str | None = None
    license: str | None = None
    license_url: str | None = None
    rights: dict = Field(default_factory=dict)


class GlyphAssetSchema(BaseModel):
    type: Literal["raster", "svg", "generated"]
    url: str
    width: int = Field(gt=0)
    height: int = Field(gt=0)
    bbox: list[float] = Field(min_length=4, max_length=4)


class GlyphTransformSchema(BaseModel):
    x: float = 0
    y: float = 0
    scaleX: float = 1
    scaleY: float = 1
    rotation: float = 0
    skewX: float = 0
    skewY: float = 0


class GlyphAppearanceSchema(BaseModel):
    opacity: float = Field(default=1, ge=0, le=1)
    blendMode: str = "source-over"


class GlyphProvenanceSchema(BaseModel):
    type: Literal["original", "font", "fallback", "generated"] = "original"
    confidence: float | None = Field(default=None, ge=0, le=1)


class GlyphRead(BaseModel):
    id: str
    character: str
    source: GlyphSourceSchema
    asset: GlyphAssetSchema
    transform: GlyphTransformSchema = Field(default_factory=GlyphTransformSchema)
    appearance: GlyphAppearanceSchema = Field(default_factory=GlyphAppearanceSchema)
    provenance: GlyphProvenanceSchema = Field(default_factory=GlyphProvenanceSchema)


class GlyphListResponse(BaseModel):
    items: list[GlyphRead]
    total: int
    limit: int
    offset: int


class MetadataItem(BaseModel):
    id: int
    name: str


class MetadataResponse(BaseModel):
    calligraphers: list[MetadataItem]
    styles: list[MetadataItem]
    dynasties: list[MetadataItem]
    datasets: list[str]


class GlyphInstance(GlyphRead):
    glyph_id: str


class CanvasConfig(BaseModel):
    width: int = Field(default=1200, ge=100, le=12000)
    height: int = Field(default=800, ge=100, le=12000)
    background: str = "#ffffff"


class ProjectDocument(BaseModel):
    version: Literal[1] = 1
    canvas: CanvasConfig = Field(default_factory=CanvasConfig)
    glyphs: list[GlyphInstance] = Field(default_factory=list)


class ProjectCreate(BaseModel):
    name: str = Field(default="Untitled", min_length=1, max_length=240)
    document: ProjectDocument


class ProjectUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=240)
    document: ProjectDocument | None = None


class ProjectRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: str
    name: str
    document: ProjectDocument


class ProjectListItem(BaseModel):
    id: str
    name: str


class HealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["ok"]
    glyphs: int


class ImportResult(BaseModel):
    imported: int
    skipped: int
    failed: int
    errors: list[str] = Field(default_factory=list)

    @field_validator("errors")
    @classmethod
    def cap_errors(cls, errors: list[str]) -> list[str]:
        return errors[:50]

class SimilarGlyphItem(BaseModel):
    glyph: GlyphRead
    score: float = Field(ge=-1, le=1)


class SimilarityResponse(BaseModel):
    target_id: str
    model_name: str
    items: list[SimilarGlyphItem]


class EmbeddingIndexResult(BaseModel):
    model_name: str
    indexed: int
    skipped: int
    failed: int
    errors: list[str] = Field(default_factory=list)


class BatchComposeRequest(BaseModel):
    text: str = Field(min_length=1, max_length=20000)
    layout: Literal["grid", "vertical-rtl", "horizontal-ltr"] = "grid"
    columns: int = Field(default=6, ge=1, le=50)
    cell_width: float = Field(default=180, gt=20, le=2000)
    cell_height: float = Field(default=180, gt=20, le=2000)
    gap_x: float = Field(default=0, ge=-100, le=500)
    gap_y: float = Field(default=0, ge=-100, le=500)
    start_x: float = 80
    start_y: float = 80
    calligrapher: str | None = None
    style: str | None = None
    dataset: str | None = None
    use_structural_fallback: bool = True


class BatchPlacement(BaseModel):
    glyph: GlyphInstance
    line: int
    column: int


class BatchComposeResponse(BaseModel):
    placements: list[BatchPlacement]
    missing: list[str]
    total_characters: int
    resolved_characters: int
