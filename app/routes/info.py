from flask import Blueprint, render_template, redirect, url_for
from ..auth import get_authenticated_user
from ..services.device import get_device_info
from ..services.system import get_system_info

router = Blueprint('info', __name__)


@router.route("/info")
def info():
    try:
        user = get_authenticated_user()
        status = get_system_info()
        device = get_device_info()
        return render_template(
            "info.html",
            username=user["username"],
            status=status,
            device=device,
        )
    except Exception:
        return redirect(url_for('auth.login_page'))
