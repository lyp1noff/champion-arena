from fastapi import APIRouter, Depends, Form, UploadFile, File, HTTPException
from src.dependencies.auth import get_current_user
from src.services.storage import upload_file_to_r2

router = APIRouter(
    prefix="/upload", tags=["Upload"], dependencies=[Depends(get_current_user)]
)


@router.post("/photo")
async def upload_photo(file: UploadFile = File(...), path: str = Form(...)):
    file_content = await file.read()

    if not file_content:
        raise HTTPException(status_code=400, detail="Empty file")

    file_url = await upload_file_to_r2(file_content, path)

    if not file_url:
        raise HTTPException(status_code=500, detail="Error uploading to R2")

    return {"url": file_url}
