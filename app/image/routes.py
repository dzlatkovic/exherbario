"""
This module defines the endpoints for the Image API, which
allows users to upload, retrieve, and delete images associated
with specimens in the herbarium.
"""


from typing import List, Dict

from fastapi import APIRouter, Depends, UploadFile, File

from app.image.controller import ImageController, PlantNetController
from app.image.schemas import ImageSchema, PlantNetResultSchema, Organs
from app.image.schemas import ImageType
from app.users.controller import JWTBearer

image_router = APIRouter(prefix="/api/image", tags=["Image"])


@image_router.post("/upload-image", response_model=ImageSchema,
                   dependencies=[Depends(JWTBearer("super_user"))])
def upload_image(specimen_id: str, image_type: ImageType, file: UploadFile = File(...)):
    """
    Uploads a new image file for the specified specimen.

    :param specimen_id: The ID of the specimen to associate the image with.
    :param image_type: The type of the image (field, herbarium, macro, microscope).
    :param file: The image file to upload.
    :return: The newly created image schema.
    """
    return ImageController.create_image(specimen_id, image_type, file)


@image_router.get("/get-image/{image_id}", dependencies=[Depends(JWTBearer())], response_model=ImageSchema)
def get_image_by_id(image_id: str):
    """
    Retrieves an image by its ID.

    :param image_id: The ID of the image to retrieve.
    :return: The retrieved image schema.
    """
    return ImageController.get_image_by_id(image_id)


@image_router.get("/get-all_images/{specimen_id}", dependencies=[Depends(JWTBearer())], response_model=List[ImageSchema])
def get_all_images(specimen_id: str):
    """
    Retrieves all images associated with the specified specimen.

    :param specimen_id: The ID of the specimen to retrieve images for.
    :return: A list of image schemas.
    """
    return ImageController.get_all_images_for_specimen(specimen_id)


@image_router.delete("/delete-image",
                     dependencies=[Depends(JWTBearer("super_user"))])
def delete_weather_data(image_id: str):
    """
    Deletes an image by its ID, removes the associated file from storage,
    and deletes the reference to the file from the database.

    :param image_id: The ID of the image to delete.
    :return: A response indicating success or failure.
    """
    return ImageController.delete_image(image_id)


plantnet_router = APIRouter(prefix="/api/plantnet", tags=["PlantNet"])


@plantnet_router.post("/save-plantnet-identification", response_model=PlantNetResultSchema,
                      dependencies=[Depends(JWTBearer("super_user"))])
def save_plantnet_identification(image_id: str, organs: Organs):
    """
    Saves the results of a PlantNet identification to the database.

    :param image_id: The ID of the image that was identified.
    :param organs: An object representing the organs that were identified in the image.
    :return: The saved PlantNetResult object.
    """
    return PlantNetController.save_plantnet_identification(image_id, organs)


@plantnet_router.get("/get-result/{result_id}", dependencies=[Depends(JWTBearer())], response_model=PlantNetResultSchema)
def get_image_by_id(result_id: str):
    """
    Retrieves a PlantNet result by its ID.

    :param result_id: The ID of the PlantNet result to retrieve.
    :return: The PlantNetResult object.
    """
    return PlantNetController.get_id_result_by_id(result_id)


@plantnet_router.delete("/delete-id-result",
                        dependencies=[Depends(JWTBearer("super_user"))])
def delete_weather_data(result_id: str):
    """
    Deletes a PlantNet identification result from the database by its ID.

    :param result_id: The ID of the PlantNet result to delete.
    :return: None
    """
    return PlantNetController.delete_plantnet_identification(result_id)


@plantnet_router.get("/get-all-results-for-image/{image_id}", dependencies=[Depends(JWTBearer())], response_model=List[PlantNetResultSchema])
def get_all_results_for_image(image_id: str):
    """
    Retrieves all PlantNet results for an image with the given ID.

    :param image_id: The ID of the image to retrieve PlantNet results for.
    :return: A list of PlantNetResult objects.
    """
    return PlantNetController.get_plantnet_result_for_image(image_id)


@plantnet_router.get("/get-all-results-for-specimen/{specimen_id}", dependencies=[Depends(JWTBearer())],
                     response_model=List[PlantNetResultSchema])
def get_all_results_for_specimen(specimen_id: str):
    """
    Retrieves all PlantNet results for a specimen with the given ID.

    :param specimen_id: The ID of the specimen to retrieve PlantNet results for.
    :return: A list of PlantNetResult objects.
    """
    return PlantNetController.get_plantnet_result_for_specimen(specimen_id)


@plantnet_router.get("/get-plantnet-results-with-mismatched-taxonomy", dependencies=[Depends(JWTBearer())],
                     response_model=List[Dict[str, str]])
def get_plantnet_results_with_mismatched_taxonomy():
    """
    Retrieves all PlantNet results for specimens whose GBIF key in the taxonomy table
    does not match the GBIF ID in the PlantNet results, and joins the results with
    other relevant tables.

    :return: A JSON response containing a list of dictionaries with the relevant
    fields from the database.
    """
    results = PlantNetController.get_plantnet_results_with_mismatched_taxonomy()
    return results
