from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.responses import FileResponse

from ..models.device import DeviceActionRequest
from ..services.device import get_device_info, perform_device_action
from ..services.storage import (
    STORAGE_DIR,
    delete_storage_path,
    get_storage_file_path,
    list_storage_files,
    save_upload_file,
    storage_summary,
)
from ..services.system import get_system_info

router = APIRouter()


@router.get("/status")
async def status():
    return get_system_info()


@router.get("/device")
async def device_status():
    return get_device_info()


@router.post("/device/action")
async def device_action(request: DeviceActionRequest):
    try:
        return perform_device_action(request.action)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage")
async def storage_list(path: str = ""):
    try:
        return {"summary": storage_summary(), "items": list_storage_files(path)}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post("/storage/upload")
async def storage_upload(file: UploadFile = File(...), path: str = Form("")):
    try:
        target = save_upload_file(path, file)
        relative_path = str(target.relative_to(STORAGE_DIR))
        return {"path": relative_path.replace('\\', '/')}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage/download")
async def storage_download(path: str):
    try:
        target = get_storage_file_path(path)
        return FileResponse(target, media_type="application/octet-stream", filename=target.name)
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado")


@router.post("/storage/delete")
async def storage_delete(path: str = Form(...)):
    try:
        delete_storage_path(path)
        return {"deleted": path}
    except FileNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado")
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
