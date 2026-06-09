from pathlib import Path
from flask import Blueprint, render_template, redirect, url_for
from ..auth import get_authenticated_user

from ..services.device import get_device_info
from ..services.storage import storage_summary
from ..services.system import get_system_info

router = Blueprint('dashboard', __name__)

@router.route("/")
def home():
    try:
        user = get_authenticated_user()
        status = get_system_info()
        device = get_device_info()
        storage = storage_summary(user["id"])
        return render_template(
            "index.html",
            status=status,
            device=device,
            storage_summary=storage,
        )
    except Exception:
        return redirect(url_for('auth.login_page'))
