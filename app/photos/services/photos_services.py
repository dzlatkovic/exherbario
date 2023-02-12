from app.photos.models import Photos
from app.db import SessionLocal
from app.photos.repository import PhotosRepository


class PhotosService:

    @staticmethod
    def create_new_photos(field_photo: str, specimen_photo: str) -> Photos:
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.create_photos(field_photo, specimen_photo)
        except Exception as e:
            raise e

    @staticmethod
    def read_all_photos():
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.read_all_photos()
        except Exception as e:
            raise e

    @staticmethod
    def read_photos_by_id(photos_id: str):
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.read_photos_by_id(photos_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_photos_by_id(photos_id: str):
        try:
            with SessionLocal() as db:
                repository = PhotosRepository(db)
                return repository.delete_photos(photos_id)
        except Exception as e:
            raise e
