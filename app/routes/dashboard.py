from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader, select_autoescape

BASE_DIR = Path(__file__).resolve().parent.parent
templates = Environment(
    loader=FileSystemLoader(BASE_DIR / "templates"),
    autoescape=select_autoescape(["html", "xml"]),
)

from ..services.device import get_device_info
from ..services.storage import storage_summary
from ..services.system import get_system_info

router = APIRouter()


@router.get("/", response_class=HTMLResponse)
async def home(request: Request):
    status = get_system_info()
    device = get_device_info()
    storage = storage_summary()
    template = templates.get_template("index.html")
    return HTMLResponse(
        template.render(
            request=request,
            status=status,
            device=device,
            storage_summary=storage,
        )
    )
