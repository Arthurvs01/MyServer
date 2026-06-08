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
from ..services.device import get_device_info
from ..services.system import get_system_info

router = APIRouter()


@router.get("/info")
async def info(request: Request):
    try:
        user = get_authenticated_user(request)
        status = get_system_info()
        device = get_device_info()
        template = templates.get_template("info.html")
        return HTMLResponse(
            template.render(
                request=request,
                username=user["username"],
                status=status,
                device=device,
            )
        )
    except Exception:
        return RedirectResponse(url="/login", status_code=302)
