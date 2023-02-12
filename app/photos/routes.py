from fastapi import APIRouter

from app.photos.controller import PhotosController
from app.photos.schemas import PhotosSchema, PhotosSchemaIn

photos_router = APIRouter(prefix="/api/photos", tags=["Photos"])


@photos_router.post("/create-new-photos", response_model=PhotosSchema)
def create_new_field_loc(photos: PhotosSchemaIn):
    return PhotosController.create_new_photos(field_photo=photos.field_photo,
                                              specimen_photo=photos.specimen_photo)


@photos_router.get("/get-all-photos", response_model=list[PhotosSchema])
def get_all_photos():
    photos = PhotosController.get_all_photos()
    return photos


@photos_router.get("/get-photos-by-id", response_model=PhotosSchema)
def get_field_loc_by_id(field_loc_id: str):
    return PhotosController.get_photos_by_id(field_loc_id)


@photos_router.delete("/delete-photos")
def delete_photos_by_id(photos_id: str):
    return PhotosController.delete_photos_by_id(photos_id)
