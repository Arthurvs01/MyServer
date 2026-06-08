from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
APP_NAME = "CasaPy"
APP_VERSION = "0.1.0"
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"
STORAGE_DIR = BASE_DIR / "storage"
APP_HOST = "::"
APP_PORT = 8080
