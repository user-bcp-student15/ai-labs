from fastapi import APIRouter, Depends, File, HTTPException, Request, UploadFile

from app.schemas import Identity, UploadResponse
from app.security import legacy_identity
from app.services.uploads import UploadRejectedError, store_upload

router = APIRouter(prefix="/api")


@router.post("/requirements", status_code=201)
async def upload_requirement(
    request: Request,
    file: UploadFile = File(...),
    identity: Identity = Depends(legacy_identity),
) -> UploadResponse:
    try:
        stored = await store_upload(request.app.state.settings.upload_dir, file)
    except UploadRejectedError as error:
        raise HTTPException(status_code=error.status, detail=error.message) from error
    return UploadResponse(owner=identity.username, file_name=stored.file_name, stored_at=stored.file_name, size=stored.size)
