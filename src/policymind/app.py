import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from policymind.api.routes import router
from policymind.dependencies.container import AppContainer, build_container


_container: AppContainer | None = None


def get_container_from_app() -> AppContainer:
    if _container is None:
        raise RuntimeError("Container has not been initialized.")
    return _container


def create_app() -> FastAPI:
    app = FastAPI(title="PolicyMind API")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def startup_event() -> None:
        global _container
        _container = build_container()
        os.makedirs(_container.settings.UPLOAD_DIR, exist_ok=True)
        if _container.settings.VECTOR_DB_TYPE == "faiss":
            os.makedirs(_container.settings.VECTOR_STORE_DIR, exist_ok=True)

    app.include_router(router)
    return app


app = create_app()

