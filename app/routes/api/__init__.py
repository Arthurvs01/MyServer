from fastapi import APIRouter, File, Form, HTTPException, Request, UploadFile, status
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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage")
async def storage_list(request: Request, path: str = ""):
    user = get_authenticated_user(request)
    try:
        return {
            "summary": storage_summary(user["id"]),
            "items": list_storage_files(user["id"], path),
        }
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


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
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/storage/download")
async def storage_download(request: Request, path: str):
    user = get_authenticated_user(request)
    try:
        target = get_storage_file_path(user["id"], path)
        return FileResponse(target, media_type="application/octet-stream", filename=target.name)
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado"
        )


@router.post("/storage/delete")
async def storage_delete(request: Request, path: str = Form(...)):
    user = get_authenticated_user(request)
    try:
        delete_storage_path(user["id"], path)
        return {"deleted": path}
    except FileNotFoundError:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Arquivo não encontrado"
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
