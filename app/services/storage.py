from pathlib import Path
from typing import Dict, List

from fastapi import UploadFile

from ..config import STORAGE_DIR

STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_user_storage_dir(user_id: int) -> Path:
    user_dir = STORAGE_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def resolve_storage_path(user_id: int, relative_path: str = "") -> Path:
    user_dir = get_user_storage_dir(user_id)
    if not relative_path:
        return user_dir
    target = (user_dir / relative_path).resolve()
    if user_dir not in target.parents and target != user_dir:
        raise ValueError("Caminho fora da pasta de armazenamento do usuário")
    return target


def list_storage_files(user_id: int, relative_path: str = "") -> List[Dict[str, str]]:
    root = resolve_storage_path(user_id, relative_path)
    items: List[Dict[str, str]] = []
    if not root.exists():
        return items
    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        item_type = "directory" if entry.is_dir() else "file"
        items.append(
            {
                "name": entry.name,
                "path": str(entry.relative_to(get_user_storage_dir(user_id))).replace(
                    "\\", "/"
                ),
                "type": item_type,
                "size": str(entry.stat().st_size) if entry.is_file() else "0",
            }
        )
    return items


def storage_summary(user_id: int) -> Dict[str, str]:
    user_dir = get_user_storage_dir(user_id)
    total_size = 0
    total_files = 0
    if user_dir.exists():
        for path in user_dir.rglob("*"):
            if path.is_file():
                total_files += 1
                total_size += path.stat().st_size
    return {
        "root": str(user_dir),
        "total_files": str(total_files),
        "total_size_bytes": str(total_size),
    }


def get_user_storage_summary(user_id: int) -> Dict[str, str]:
    return storage_summary(user_id)


def save_upload_file(user_id: int, relative_path: str, upload_file: UploadFile) -> Path:
    if relative_path:
        target_folder = resolve_storage_path(user_id, relative_path)
        if target_folder.exists() and target_folder.is_file():
            raise ValueError("O caminho de upload não pode ser um arquivo existente")
        target_folder.mkdir(parents=True, exist_ok=True)
        target = target_folder / upload_file.filename
    else:
        user_dir = get_user_storage_dir(user_id)
        target = user_dir / upload_file.filename
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open("wb") as buffer:
        buffer.write(upload_file.file.read())
    return target


def delete_storage_path(user_id: int, relative_path: str) -> None:
    target = resolve_storage_path(user_id, relative_path)
    if target.is_dir():
        for child in target.iterdir():
            if child.is_file():
                child.unlink()
            else:
                delete_storage_path(
                    user_id, str(child.relative_to(get_user_storage_dir(user_id)))
                )
        target.rmdir()
    else:
        target.unlink()


def get_storage_file_path(user_id: int, relative_path: str) -> Path:
    target = resolve_storage_path(user_id, relative_path)
    if not target.exists() or not target.is_file():
        raise FileNotFoundError("Arquivo de armazenamento não encontrado")
    return target
