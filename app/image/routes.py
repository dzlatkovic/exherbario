from typing import List

from fastapi import APIRouter, UploadFile, File

from app.image.controller import ImageController
from app.image.schemas import ImageSchema
from app.image.schemas import ImageType

image_router = APIRouter(prefix="/api/image", tags=["Image"])


@image_router.post("/upload-image", response_model=ImageSchema)
def upload_image(specimen_id: str, image_type: ImageType, file: UploadFile = File(...)):
    return ImageController.create_image(specimen_id, image_type, file)


@image_router.get("/get-image/{image_id}", response_model=ImageSchema)
def get_image_by_id(image_id: str):
    return ImageController.get_image_by_id(image_id)


@image_router.get("/get-all_images/{specimen_id}", response_model=List[ImageSchema])
def get_all_images(specimen_id: str):
    return ImageController.get_all_images_for_specimen(specimen_id)


@image_router.delete("/delete-image")
def delete_weather_data(image_id: str):
    return ImageController.delete_image(image_id)
