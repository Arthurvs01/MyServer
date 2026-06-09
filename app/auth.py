from flask import request, abort

def get_authenticated_user() -> dict:
    user_id = request.cookies.get("user_id")
    username = request.cookies.get("username")
    if not user_id or not username:
        abort(401, description="Não autenticado")
    return {"id": int(user_id or 0), "username": str(username or "")}


def require_auth() -> dict:
    return get_authenticated_user()
