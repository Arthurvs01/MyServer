from .config import APP_HOST, APP_PORT
from .server import app


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host=APP_HOST, port=APP_PORT, log_level="info")
