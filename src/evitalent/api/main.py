from __future__ import annotations

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from evitalent.api.routes import assistant, audits, extraction, fixtures, health, official_samples, rankings, resumes
from evitalent.db import init_db


def create_app() -> FastAPI:
    app = FastAPI(title="EviTalent-Rank API", version="1.0.0")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1", "http://localhost", "http://127.0.0.1:8501", "http://localhost:8501"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.include_router(health.router)
    app.include_router(resumes.router)
    app.include_router(extraction.router)
    app.include_router(fixtures.router)
    app.include_router(rankings.router)
    app.include_router(audits.router)
    app.include_router(official_samples.router)
    app.include_router(assistant.router)

    @app.on_event("startup")
    def startup() -> None:
        init_db()

    return app


app = create_app()
