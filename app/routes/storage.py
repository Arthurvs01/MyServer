from flask import Blueprint, render_template, redirect, url_for
from ..auth import get_authenticated_user
from ..services.storage import get_user_storage_summary

router = Blueprint('storage', __name__)


@router.route("/storage")
def storage():
    try:
        user = get_authenticated_user()
        storage = get_user_storage_summary(user["id"])
        return render_template(
            "storage.html",
            username=user["username"],
            storage_summary=storage
        )
    except Exception:
        return redirect(url_for('auth.login_page'))
