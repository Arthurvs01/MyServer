from pathlib import Path

from fastapi import APIRouter, Form, HTTPException, Request, Response, status
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent.parent.parent
templates = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

from ...db import create_user, user_exists, verify_user
from ...models.user import hash_password, verify_password

router = APIRouter()


@router.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    template = templates.get_template("login.html")
    return template.render(request=request)


@router.post("/login", response_class=HTMLResponse)
async def login(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
):
    password_hash = hash_password(password)
    user = verify_user(username, password_hash)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuário ou senha inválidos"
        )
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(user["id"]), httponly=True)
    response.set_cookie(key="username", value=user["username"], httponly=True)
    return response


@router.get("/register", response_class=HTMLResponse)
async def register_page(request: Request):
    template = templates.get_template("register.html")
    return template.render(request=request)


@router.post("/register")
async def register(
    request: Request,
    username: str = Form(...),
    password: str = Form(...),
    password_confirm: str = Form(...),
):
    if len(username) < 3:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Usuário deve ter pelo menos 3 caracteres",
        )
    if len(password) < 6:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Senha deve ter pelo menos 6 caracteres",
        )
    if password != password_confirm:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="As senhas não conferem"
        )
    if user_exists(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Usuário já existe"
        )
    password_hash = hash_password(password)
    user_id = create_user(username, password_hash)
    response = RedirectResponse(url="/", status_code=status.HTTP_302_FOUND)
    response.set_cookie(key="user_id", value=str(user_id), httponly=True)
    response.set_cookie(key="username", value=username, httponly=True)
    return response


@router.get("/logout")
async def logout():
    response = RedirectResponse(url="/login", status_code=status.HTTP_302_FOUND)
    response.delete_cookie("user_id")
    response.delete_cookie("username")
    return response
