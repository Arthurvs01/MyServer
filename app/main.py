from .config import APP_HOST, APP_PORT
from .server import app

if __name__ == "__main__":
    from waitress import serve
    print(f"Iniciando CasaPy (Flask) em http://{APP_HOST}:{APP_PORT}")
    serve(app, host=APP_HOST, port=APP_PORT)
