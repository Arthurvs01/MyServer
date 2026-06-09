from flask import Blueprint, render_template, request, redirect, url_for, make_response, abort
from ...db import create_user, user_exists, verify_user
from ...models.user import hash_password, verify_password

router = Blueprint('auth', __name__)


@router.route("/login", methods=["GET"])
def login_page():
    return render_template("login.html")


@router.route("/login", methods=["POST"])
def login():
    username = request.form.get("username")
    password = request.form.get("password")
    
    if not username or not password:
        abort(400, description="Usuário e senha são obrigatórios")

    password_hash = hash_password(password)
    user = verify_user(username, password_hash)
    if not user:
        abort(401, description="Usuário ou senha inválidos")

    response = make_response(redirect(url_for('home.home')))
    if user:
        response.set_cookie("user_id", str(user["id"]), httponly=True)
        response.set_cookie("username", user["username"], httponly=True)
        
    return response


@router.route("/register", methods=["GET"])
def register_page():
    return render_template("register.html")


@router.route("/register", methods=["POST"])
def register():
    username = request.form.get("username")
    password = request.form.get("password")
    password_confirm = request.form.get("password_confirm")

    if not username or not password or not password_confirm:
        abort(400, description="Todos os campos são obrigatórios")

    if len(username) < 3:
        abort(400, description="Usuário deve ter pelo menos 3 caracteres")

    if len(password) < 6:
        abort(400, description="Senha deve ter pelo menos 6 caracteres")

    if password != password_confirm:
        abort(400, description="As senhas não conferem")

    if user_exists(username):
        abort(400, description="Usuário já existe")

    password_hash = hash_password(password)
    user_id = create_user(username, password_hash)
    
    response = make_response(redirect(url_for('home.home')))
    response.set_cookie("user_id", str(user_id), httponly=True)
    response.set_cookie("username", username, httponly=True)
    return response


@router.route("/logout")
def logout():
    response = make_response(redirect(url_for('auth.login_page')))
    response.delete_cookie("user_id")
    response.delete_cookie("username")
    return response
