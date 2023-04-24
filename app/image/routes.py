from fastapi import APIRouter, UploadFile, File

from app.image.controller import ImageController
from app.image.schemas import ImageSchema

image_router = APIRouter(prefix="/api/image", tags=["Image"])


@image_router.post("/upload-image", response_model=ImageSchema)
def upload_image(specimen_id: str, file: UploadFile = File(...)):
    return ImageController.create_image(specimen_id, file)
