from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

from ..auth import get_authenticated_user

router = APIRouter()


@router.get("/")
async def home(request: Request):
    try:
        user = get_authenticated_user(request)
        template = templates.get_template("home.html")
        return HTMLResponse(template.render(request=request, username=user["username"]))
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
