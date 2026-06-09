from flask import Blueprint, render_template, redirect, url_for
from ..auth import get_authenticated_user

router = Blueprint('home', __name__)


@router.route("/")
def home():
    try:
        user = get_authenticated_user()
        return render_template("home.html", username=user["username"])
    except Exception:
        return redirect(url_for('auth.login_page'))
