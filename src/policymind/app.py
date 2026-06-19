import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

from policymind.api.routes import router
from policymind.dependencies.container import AppContainer, build_container

# Resolve frontend paths relative to project root.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
_FRONTEND_DIR = _PROJECT_ROOT / "frontend"

_container: AppContainer | None = None


def get_container_from_app() -> AppContainer:
    if _container is None:
        raise RuntimeError("Container has not been initialized.")
    return _container


def create_app() -> FastAPI:
    @asynccontextmanager
    async def lifespan(app: FastAPI):
        global _container
        _container = build_container()
        os.makedirs(_container.settings.UPLOAD_DIR, exist_ok=True)
        if _container.settings.VECTOR_DB_TYPE == "faiss":
            os.makedirs(_container.settings.VECTOR_STORE_DIR, exist_ok=True)
        yield

    app = FastAPI(title="PolicyMind API", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    app.include_router(router)

    # --- Frontend static files & page route ---
    if _FRONTEND_DIR.exists():
        # Serve CSS/JS assets at /static
        app.mount("/static", StaticFiles(directory=str(_FRONTEND_DIR / "static")), name="static")

        @app.get("/app", response_class=HTMLResponse, include_in_schema=False)
        async def serve_frontend() -> HTMLResponse:
            index_path = _FRONTEND_DIR / "index.html"
            return HTMLResponse(content=index_path.read_text(encoding="utf-8"))

    return app


app = create_app()

