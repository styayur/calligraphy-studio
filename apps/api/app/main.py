from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlalchemy import func, select

from app.config import Settings, get_settings
from app.database import Database
from app.models import Glyph
from app.routes import compose, fallback, glyphs, metadata, projects, search, similarity
from app.schemas import HealthResponse
from app.seed import seed_cursive_if_missing, seed_demo_if_empty, seed_fonts_if_missing
from app.services.embedding_service import EmbeddingService


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    config.assets_dir.mkdir(parents=True, exist_ok=True)
    database = Database(config.database_url)
    database.create_schema()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        seed_demo_if_empty(database, config)
        seed_cursive_if_missing(database, config)
        seed_fonts_if_missing(database, config)
        if config.auto_index_embeddings:
            with database.session() as session:
                EmbeddingService(config.assets_dir).index(
                    session,
                    limit=config.auto_index_limit,
                )
        yield

    app = FastAPI(
        title=config.app_name,
        version="0.1.0",
        description="Phase 1 Glyph API: import, search, compose, export.",
        lifespan=lifespan,
    )
    app.state.settings = config
    app.state.db = database

    app.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origin_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/health", response_model=HealthResponse, tags=["system"])
    def health(request: Request) -> HealthResponse:
        with request.app.state.db.session() as session:
            count = session.scalar(select(func.count()).select_from(Glyph)) or 0
        return HealthResponse(status="ok", database="ok", glyphs=count)

    app.include_router(compose.router, prefix=config.api_prefix)
    app.include_router(glyphs.router, prefix=config.api_prefix)
    app.include_router(search.router, prefix=config.api_prefix)
    app.include_router(metadata.router, prefix=config.api_prefix)
    app.include_router(projects.router, prefix=config.api_prefix)
    app.include_router(fallback.router, prefix=config.api_prefix)
    app.include_router(similarity.router, prefix=config.api_prefix)
    app.mount("/assets", StaticFiles(directory=config.assets_dir), name="assets")

    return app


app = create_app()