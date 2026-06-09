import os
import threading
from flask import Blueprint, request, jsonify, send_file, abort
from ..auth import get_authenticated_user
from ..models.device import DeviceActionRequest
from ..services.device import get_device_info, perform_device_action
from ..services.storage import (
    get_user_storage_dir,
    delete_storage_path,
    list_storage_files,
    save_upload_file,
    create_storage_directory,
    move_storage_path,
    copy_storage_path,
    rename_storage_path,
    search_storage,
    zip_storage_folder,
    resolve_storage_path,
    storage_summary,
)
from ..services.system import get_system_info

api_bp = Blueprint('api', __name__)


@api_bp.route("/status", methods=["GET"])
def status_api():
    get_authenticated_user()
    return jsonify(get_system_info())


@api_bp.route("/device", methods=["GET"])
def device_status():
    get_authenticated_user()
    return jsonify(get_device_info())


@api_bp.route("/device/action", methods=["POST"])
def device_action():
    get_authenticated_user()
    data = request.get_json()
    action = data.get("action")
    try:
        return jsonify(perform_device_action(action))
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400


@api_bp.route("/storage", methods=["GET"])
def storage_list():
    user = get_authenticated_user()
    path = request.args.get("path", "")
    try:
        return jsonify({
            "summary": storage_summary(user["id"]),
            "items": list_storage_files(user["id"], path),
        })
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400


@api_bp.route("/storage/upload", methods=["POST"])
def storage_upload():
    user = get_authenticated_user()
    file = request.files.get("file")
    path = request.form.get("path", "")
    if not file:
        abort(400, description="Nenhum arquivo enviado")
    try:
        target = save_upload_file(user["id"], path, file)
        relative_path = str(
            target.relative_to(get_user_storage_dir(user["id"]))
        ).replace("\\", "/")
        return jsonify({"path": relative_path})
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400

@api_bp.route("/storage/search", methods=["GET"])
def storage_search():
    user = get_authenticated_user()
    q = request.args.get("q", "")
    if len(q) < 2:
        return jsonify([])
    return jsonify(search_storage(user["id"], q))


@api_bp.route("/storage/rename", methods=["POST"])
def storage_rename():
    user = get_authenticated_user()
    path = request.form.get("path", "")
    new_name = request.form.get("new_name", "")
    try:
        rename_storage_path(user["id"], path, new_name)
        return jsonify({"status": "success", "new_name": new_name})
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"detail": str(exc)}), 400

@api_bp.route("/storage/move", methods=["POST"])
def storage_move():
    user = get_authenticated_user()
    path = request.form.get("path", "")
    destination = request.form.get("destination", "")
    try:
        move_storage_path(user["id"], path, destination)
        return jsonify({"status": "success"})
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"detail": str(exc)}), 400


@api_bp.route("/storage/copy", methods=["POST"])
def storage_copy():
    user = get_authenticated_user()
    path = request.form.get("path", "")
    destination = request.form.get("destination", "")
    try:
        copy_storage_path(user["id"], path, destination)
        return jsonify({"status": "success"})
    except (ValueError, FileNotFoundError) as exc:
        return jsonify({"detail": str(exc)}), 400

@api_bp.route("/storage/mkdir", methods=["POST"])
def storage_mkdir():
    user = get_authenticated_user()
    path = request.form.get("path", "")
    name = request.form.get("name", "")
    try:
        create_storage_directory(user["id"], path, name)
        return jsonify({"status": "success", "folder": name})
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400


@api_bp.route("/storage/download", methods=["GET"])
def storage_download():
    user = get_authenticated_user()
    path = request.args.get("path", "")
    try:
        target = resolve_storage_path(user["id"], path)
        if not target.exists():
            raise FileNotFoundError()
            
        if target.is_dir():
            zip_path = zip_storage_folder(user["id"], path or "")
            # Limpeza do temporário em thread separada
            threading.Timer(60.0, lambda p: os.remove(p) if os.path.exists(p) else None, args=[str(zip_path)]).start()
            return send_file(zip_path, as_attachment=True, download_name=f"{target.name}.zip")
            
        return send_file(target, as_attachment=True, download_name=target.name)
    except FileNotFoundError:
        abort(404, description="Arquivo não encontrado")


@api_bp.route("/storage/delete", methods=["POST"])
def storage_delete():
    user = get_authenticated_user()
    path = request.form.get("path", "")
    try:
        delete_storage_path(user["id"], path)
        return jsonify({"deleted": path})
    except FileNotFoundError:
        abort(404, description="Arquivo não encontrado")
    except ValueError as exc:
        return jsonify({"detail": str(exc)}), 400
