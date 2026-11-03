from collections.abc import AsyncIterator
from contextlib import asynccontextmanager, closing
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import (
    CORS_ALLOWED_HEADERS,
    CORS_ALLOWED_METHODS,
    Settings,
    load_settings,
)
from app.database import initialize_database, open_connection
from app.routes import health, requirements, tasks


def prepare_storage(settings: Settings) -> None:
    Path(settings.db_path).parent.mkdir(parents=True, exist_ok=True)
    Path(settings.upload_dir).mkdir(parents=True, exist_ok=True)
    with closing(open_connection(settings.db_path)) as connection:
        initialize_database(connection)


def create_app(db_path: str | None = None, upload_dir: str | None = None) -> FastAPI:
    settings = load_settings(db_path, upload_dir)

    @asynccontextmanager
    async def lifespan(_: FastAPI) -> AsyncIterator[None]:
        prepare_storage(settings)
        yield

    app = FastAPI(title="Workshop Requirements API", version="0.1.0", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(settings.cors_origins),
        allow_credentials=False,
        allow_methods=CORS_ALLOWED_METHODS,
        allow_headers=CORS_ALLOWED_HEADERS,
    )
    for router in (tasks.router, requirements.router, health.router):
        app.include_router(router)
    return app


app = create_app()
