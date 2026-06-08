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
from ..services.storage import get_user_storage_summary

router = APIRouter()


@router.get("/storage")
async def storage(request: Request):
    try:
        user = get_authenticated_user(request)
        storage = get_user_storage_summary(user["id"])
        template = templates.get_template("storage.html")
        return HTMLResponse(
            template.render(
                request=request, username=user["username"], storage_summary=storage
            )
        )
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
