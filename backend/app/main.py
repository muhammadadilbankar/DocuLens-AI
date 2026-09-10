from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import initialize_database


@asynccontextmanager
async def lifespan(_: FastAPI):
    settings = get_settings()
    settings.resolved_upload_directory.mkdir(parents=True, exist_ok=True)
    settings.resolved_processed_directory.mkdir(parents=True, exist_ok=True)
    settings.resolved_search_index_directory.mkdir(parents=True, exist_ok=True)
    initialize_database()
    yield


def create_application() -> FastAPI:
    settings = get_settings()
    application = FastAPI(
        title=settings.app_name,
        description="Offline-first scanned document intelligence API",
        version="0.1.0",
        debug=settings.debug,
        lifespan=lifespan,
    )
    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.include_router(api_router)
    return application


app = create_application()
