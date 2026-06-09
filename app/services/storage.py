import shutil
import tempfile
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

from werkzeug.datastructures import FileStorage

from ..config import STORAGE_DIR

STORAGE_DIR.mkdir(parents=True, exist_ok=True)


def get_user_storage_dir(user_id: int) -> Path:
    user_dir = STORAGE_DIR / f"user_{user_id}"
    user_dir.mkdir(parents=True, exist_ok=True)
    return user_dir


def resolve_storage_path(user_id: int, relative_path: str = "") -> Path:
    user_dir = get_user_storage_dir(user_id).resolve()
    if not relative_path:
        return user_dir
    
    # Remove barras iniciais para evitar que o join seja tratado como caminho absoluto
    clean_path = relative_path.lstrip("/\\")
    target = (user_dir / clean_path).resolve()
    
    # Verificação robusta de subcaminho para evitar erros em Windows/Termux
    try:
        target.relative_to(user_dir)
    except ValueError:
        raise ValueError("Caminho fora da pasta de armazenamento do usuário")
    return target


def list_storage_files(user_id: int, relative_path: str = "") -> List[Dict[str, str]]:
    root = resolve_storage_path(user_id, relative_path)
    items: List[Dict[str, str]] = []
    if not root.exists():
        return items
        
    user_root = get_user_storage_dir(user_id)
    
    for entry in sorted(root.iterdir(), key=lambda item: item.name.lower()):
        item_type = "directory" if entry.is_dir() else "file"
        stat = entry.stat()
        items.append(
            {
                "name": entry.name,
                "path": str(entry.relative_to(user_root)).replace(
                    "\\", "/"
                ),
                "type": item_type,
                "size": str(stat.st_size) if entry.is_file() else "0",
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "extension": entry.suffix.lower() if entry.is_file() else ""
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


def save_upload_file(user_id: int, relative_path: str, upload_file: FileStorage) -> Path:
    # Validação do nome do arquivo para satisfazer o Pylance e evitar erros de I/O
    if not upload_file.filename:
        raise ValueError("O arquivo enviado não possui um nome válido")
    filename = upload_file.filename

    if relative_path:
        target_folder = resolve_storage_path(user_id, relative_path)
        if target_folder.exists() and target_folder.is_file():
            raise ValueError("O caminho de upload não pode ser um arquivo existente")
        target_folder.mkdir(parents=True, exist_ok=True)
        target = target_folder / filename
    else:
        user_dir = get_user_storage_dir(user_id)
        target = user_dir / filename
    target.parent.mkdir(parents=True, exist_ok=True)
    upload_file.save(str(target))
    return target


def create_storage_directory(user_id: int, relative_path: str, folder_name: str) -> Path:
    base_path = resolve_storage_path(user_id, relative_path)
    new_dir = base_path / folder_name
    new_dir.mkdir(exist_ok=True)
    return new_dir


def move_storage_path(user_id: int, source_path: str, dest_path: str) -> Path:
    source = resolve_storage_path(user_id, source_path)
    dest_dir = resolve_storage_path(user_id, dest_path)
    if not source.exists():
        raise FileNotFoundError("Item de origem não encontrado")
    
    target = dest_dir / source.name
    return Path(shutil.move(str(source), str(target)))


def copy_storage_path(user_id: int, source_path: str, dest_path: str) -> Path:
    source = resolve_storage_path(user_id, source_path)
    dest_dir = resolve_storage_path(user_id, dest_path)
    target = dest_dir / source.name
    
    if source.is_dir():
        return Path(shutil.copytree(str(source), str(target), dirs_exist_ok=True))
    return Path(shutil.copy2(str(source), str(target)))


def rename_storage_path(user_id: int, relative_path: str, new_name: str) -> Path:
    target = resolve_storage_path(user_id, relative_path)
    if not target.exists():
        raise FileNotFoundError("Item não encontrado")
    
    new_path = target.parent / new_name
    # Validação de segurança para o novo nome
    if any(c in new_name for c in r'<>:"/\|?*'):
        raise ValueError("Nome de arquivo contém caracteres inválidos")
        
    if new_path.exists():
        raise ValueError("Um item com este nome já existe")
        
    return Path(shutil.move(str(target), str(new_path)))


def search_storage(user_id: int, query: str) -> List[Dict[str, str]]:
    user_root = get_user_storage_dir(user_id)
    query = query.lower()
    all_items = list_storage_files(user_id, "") # Pega tudo na raiz (simples)
    # Ou busca recursiva real:
    results = []
    for entry in user_root.rglob("*"):
        if query in entry.name.lower():
            stat = entry.stat()
            results.append({
                "name": entry.name,
                "path": str(entry.relative_to(user_root)).replace("\\", "/"),
                "type": "directory" if entry.is_dir() else "file",
                "size": str(stat.st_size) if entry.is_file() else "0",
                "modified": datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).isoformat(),
                "extension": entry.suffix.lower() if entry.is_file() else ""
            })
    return results


def zip_storage_folder(user_id: int, relative_path: str) -> Path:
    folder_to_zip = resolve_storage_path(user_id, relative_path)
    if not folder_to_zip.is_dir():
        raise ValueError("O caminho especificado não é uma pasta")
    
    temp_dir = Path(tempfile.gettempdir()) / "casapy_zips"
    temp_dir.mkdir(parents=True, exist_ok=True)
    
    zip_name = f"{folder_to_zip.name}_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}"
    zip_base_path = temp_dir / zip_name
    
    archive_path = shutil.make_archive(str(zip_base_path), 'zip', folder_to_zip)
    return Path(archive_path)


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
