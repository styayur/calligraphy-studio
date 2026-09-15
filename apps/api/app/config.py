from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

PROJECT_ROOT = Path(__file__).resolve().parents[3]


def _default_database_url() -> str:
    database_path = (PROJECT_ROOT / "data" / "calligraphy.db").resolve()
    return f"sqlite:///{database_path.as_posix()}"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=PROJECT_ROOT / ".env",
        env_prefix="CALLISTUDIO_",
        extra="ignore",
    )

    app_name: str = "Calligraphy Studio API"
    api_prefix: str = "/api"
    database_url: str = Field(default_factory=_default_database_url)
    assets_dir: Path = Field(default_factory=lambda: PROJECT_ROOT / "storage" / "assets")
    demo_manifest: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "samples" / "demo" / "manifest.csv"
    )
    cursive_sample_root: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "samples" / "cursive" / "raw"
    )
    hanzi_data_dir: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "data" / "hanzi-writer"
    )
    font_manifest: Path = Field(
        default_factory=lambda: PROJECT_ROOT / "samples" / "fonts" / "manifest.json"
    )
    seed_demo: bool = True
    seed_cursive: bool = True
    seed_fonts: bool = True
    include_noncommercial_fonts: bool = True
    auto_index_embeddings: bool = True
    auto_index_limit: int = 5000
    fetch_remote_hanzi: bool = True
    cors_origins: str = "http://localhost:5173,http://127.0.0.1:5173"

    @property
    def cors_origin_list(self) -> list[str]:
        return [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    return Settings()