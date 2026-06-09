from pathlib import Path
from flask import Flask
from .config import APP_NAME, STORAGE_DIR
from .db import init_db
from .routes.auth import router as auth_router
from .routes.home import router as home_router
from .routes.info import router as info_router
from .routes.storage import router as storage_page_router
from .routes.api import api_bp

BASE_DIR = Path(__file__).resolve().parent

def create_app() -> Flask:
    init_db()
    app = Flask(__name__, 
                static_folder=str(BASE_DIR / "static"), 
                template_folder=str(BASE_DIR / "templates"),
                static_url_path='/static')
    
    app.register_blueprint(auth_router)
    app.register_blueprint(home_router)
    app.register_blueprint(info_router)
    app.register_blueprint(storage_page_router)
    app.register_blueprint(api_bp, url_prefix="/api")
    
    return app


app = create_app()
