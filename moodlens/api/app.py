from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse

from .routes import detect_scene, enhance, health

_STATIC = Path(__file__).parent.parent / "static"


def create_app() -> FastAPI:
    application = FastAPI(
        title="MoodLens API",
        description="AI-powered photo mood enhancement — Claude Haiku interprets your mood, Pillow applies the grade",
        version="0.1.0",
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_methods=["GET", "POST"],
        allow_headers=["*"],
    )

    @application.get("/", include_in_schema=False)
    def root() -> HTMLResponse:
        return HTMLResponse((_STATIC / "index.html").read_text())

    application.include_router(health.router, tags=["health"])
    application.include_router(enhance.router, prefix="/api/v1", tags=["enhance"])
    application.include_router(detect_scene.router, prefix="/api/v1", tags=["scene"])

    return application


app = create_app()
