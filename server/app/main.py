"""FastAPI application factory: middleware, routers, health, static SPA."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles

from .config import get_settings
from .db import ping
from .routers import account, auth, curriculum, labs, notes, projects, quiz, reports, resources, search, tutor

logger = logging.getLogger("algo-study")


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    # Create schema on boot for fresh installs; Alembic owns changes after that.
    from .db import get_engine
    from .models import Base

    Base.metadata.create_all(get_engine())
    logger.info("database ready (ai_configured=%s)", settings.ai_configured)
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.app_name, version="0.1.0", lifespan=lifespan, docs_url="/api/docs", openapi_url="/api/openapi.json")

    # Same-origin app; CORS is opened only for the configured dev origin.
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[settings.app_origin],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def security_headers(request: Request, call_next):
        response = await call_next(request)
        response.headers.setdefault("X-Content-Type-Options", "nosniff")
        response.headers.setdefault("Referrer-Policy", "same-origin")
        if request.url.path.startswith("/api/"):
            response.headers.setdefault("Cache-Control", "private, no-store")
        return response

    @app.get("/api/health")
    def health():
        db_ok = False
        try:
            db_ok = ping()
        except Exception:  # pragma: no cover - reported, not raised
            logger.exception("health: database ping failed")
        settings = get_settings()
        return {
            "ok": db_ok,
            "database": db_ok,
            "ai_configured": settings.ai_configured,
            "mode": "education-and-research-only",
            "execution": "none",
        }

    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    app.include_router(account.router, prefix="/api", tags=["account"])
    app.include_router(curriculum.router, prefix="/api/curriculum", tags=["curriculum"])
    app.include_router(resources.router, prefix="/api/resources", tags=["resources"])
    app.include_router(notes.router, prefix="/api/notes", tags=["notes"])
    app.include_router(quiz.router, prefix="/api/quiz", tags=["quiz"])
    app.include_router(labs.router, prefix="/api/labs", tags=["labs"])
    app.include_router(projects.router, prefix="/api/projects", tags=["projects"])
    app.include_router(tutor.router, prefix="/api/tutor", tags=["tutor"])
    app.include_router(search.router, prefix="/api/search", tags=["search"])
    app.include_router(reports.router, prefix="/api/reports", tags=["reports"])

    @app.exception_handler(Exception)
    async def unhandled(request: Request, exc: Exception):
        logger.exception("unhandled error on %s", request.url.path)
        return JSONResponse(status_code=500, content={"error": "Internal server error."})

    # Serve the built SPA when present (production single-process deploy).
    import os

    spa_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "web", "dist")
    if os.path.isfile(os.path.join(spa_dir, "index.html")):
        assets_dir = os.path.join(spa_dir, "assets")
        if os.path.isdir(assets_dir):
            app.mount("/assets", StaticFiles(directory=assets_dir), name="spa-assets")

        @app.get("/{full_path:path}", include_in_schema=False)
        def spa_fallback(full_path: str):
            # Client-side routes (/reports, /lessons/xyz) have no matching
            # file; serve index.html so the SPA router handles them. Real
            # files (favicon.svg, source-mapped assets) are served directly,
            # and anything outside spa_dir 404s rather than leaking.
            candidate = os.path.normpath(os.path.join(spa_dir, full_path))
            if full_path and os.path.isfile(candidate) and candidate.startswith(spa_dir + os.sep):
                return FileResponse(candidate)
            return FileResponse(os.path.join(spa_dir, "index.html"))

    return app


app = create_app()
