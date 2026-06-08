from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import APP_NAME, STORAGE_DIR
from .db import init_db
from .routes.auth import router as auth_router
from .routes.home import router as home_router
from .routes.info import router as info_router
from .routes.storage import router as storage_page_router
from .routes.api import router as api_router

BASE_DIR = Path(__file__).resolve().parent


def create_app() -> FastAPI:
    init_db()
    app = FastAPI(title=APP_NAME)
    app.mount(
        "/static",
        StaticFiles(directory=BASE_DIR / "static"),
        name="static",
    )
    app.include_router(auth_router)
    app.include_router(home_router)
    app.include_router(info_router)
    app.include_router(storage_page_router)
    app.include_router(api_router, prefix="/api")
    return app


app = create_app()
