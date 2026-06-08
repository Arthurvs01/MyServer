from fastapi import Request, HTTPException, status


def get_authenticated_user(request: Request) -> dict:
    user_id = request.cookies.get("user_id")
    username = request.cookies.get("username")
    if not user_id or not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Não autenticado",
            headers={"Location": "/login"},
        )
    return {"id": int(user_id), "username": username}


def require_auth(request: Request) -> dict:
    return get_authenticated_user(request)
