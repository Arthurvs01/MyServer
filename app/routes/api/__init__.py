import os
from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, BackgroundTasks, status as http_status
from fastapi.responses import FileResponse

from ...auth import get_authenticated_user
from ...models.device import DeviceActionRequest
from ...services.device import get_device_info, perform_device_action
from ...services.storage import (
    get_user_storage_dir,
    delete_storage_path,
    get_storage_file_path,
    list_storage_files,
    save_upload_file,
    create_storage_directory,
    zip_storage_folder,
    resolve_storage_path,
    storage_summary,
)
from ...services.system import get_system_info

router = APIRouter()


@router.get("/status")
async def status(request: Request):
    get_authenticated_user(request)
    return get_system_info()


@router.get("/device")
async def device_status(request: Request):
    get_authenticated_user(request)
    return get_device_info()


@router.post("/device/action")
async def device_action(request: Request, req: DeviceActionRequest):
    get_authenticated_user(request)
    try:
        return perform_device_action(req.action)
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage")
async def storage_list(request: Request, path: str = ""):
    user = get_authenticated_user(request)
    try:
        return {
            "summary": storage_summary(user["id"]),
            "items": list_storage_files(user["id"], path),
        }
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/storage/upload")
async def storage_upload(
    request: Request, file: UploadFile = File(...), path: str = Form("")
):
    user = get_authenticated_user(request)
    try:
        target = save_upload_file(user["id"], path, file)
        relative_path = str(
            target.relative_to(get_user_storage_dir(user["id"]))
        ).replace("\\", "/")
        return {"path": relative_path}
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/storage/mkdir")
async def storage_mkdir(request: Request, path: str = Form(""), name: str = Form(...)):
    user = get_authenticated_user(request)
    try:
        create_storage_directory(user["id"], path, name)
        return {"status": "success", "folder": name}
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage/download")
async def storage_download(request: Request, path: str, background_tasks: BackgroundTasks):
    user = get_authenticated_user(request)
    try:
        target = resolve_storage_path(user["id"], path)
        if not target.exists():
            raise FileNotFoundError()
            
        if target.is_dir():
            zip_path = zip_storage_folder(user["id"], path)
            # Remove o arquivo temporário após o envio
            background_tasks.add_task(lambda p: os.remove(p) if os.path.exists(p) else None, str(zip_path))
            return FileResponse(zip_path, media_type="application/zip", filename=f"{target.name}.zip")
            
        return FileResponse(target, media_type="application/octet-stream", filename=target.name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado"
        )


@router.post("/storage/delete")
async def storage_delete(request: Request, path: str = Form(...)):
    user = get_authenticated_user(request)
    try:
        delete_storage_path(user["id"], path)
        return {"deleted": path}
    except FileNotFoundError:
        raise HTTPException(
            status_code=http_status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado"
        )
    except ValueError as exc:
        raise HTTPException(status_code=http_status.HTTP_400_BAD_REQUEST, detail=str(exc))
