"""
This module defines the endpoints for the Image API, which
allows users to upload, retrieve, and delete images associated
with specimens in the herbarium.
"""


from typing import List

from fastapi import APIRouter, UploadFile, File

from app.image.controller import ImageController
from app.image.schemas import ImageSchema
from app.image.schemas import ImageType

image_router = APIRouter(prefix="/api/image", tags=["Image"])


@image_router.post("/upload-image", response_model=ImageSchema)
def upload_image(specimen_id: str, image_type: ImageType, file: UploadFile = File(...)):
    """
    Uploads a new image file for the specified specimen.

    :param specimen_id: The ID of the specimen to associate the image with.
    :param image_type: The type of the image (field, herbarium, macro, microscope).
    :param file: The image file to upload.
    :return: The newly created image schema.
    """
    return ImageController.create_image(specimen_id, image_type, file)


@image_router.get("/get-image/{image_id}", response_model=ImageSchema)
def get_image_by_id(image_id: str):
    """
    Retrieves an image by its ID.

    :param image_id: The ID of the image to retrieve.
    :return: The retrieved image schema.
    """
    return ImageController.get_image_by_id(image_id)


@image_router.get("/get-all_images/{specimen_id}", response_model=List[ImageSchema])
def get_all_images(specimen_id: str):
    """
    Retrieves all images associated with the specified specimen.

    :param specimen_id: The ID of the specimen to retrieve images for.
    :return: A list of image schemas.
    """
    return ImageController.get_all_images_for_specimen(specimen_id)


@image_router.delete("/delete-image")
def delete_weather_data(image_id: str):
    """
    Deletes an image by its ID, removes the associated file from storage,
    and deletes the reference to the file from the database.

    :param image_id: The ID of the image to delete.
    :return: A response indicating success or failure.
    """
    return ImageController.delete_image(image_id)
