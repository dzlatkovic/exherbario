from app.storage.models import Storage
from app.db import SessionLocal
from app.storage.repository import StorageRepository
from app.storage.exceptions import StorageExceptionBox


class StorageService:

    @staticmethod
    def create_new_storage(room: str, shelf: str, box: str) -> StorageExceptionBox or Storage:
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                storage = repository.read_storage_by_box(box)
                if storage is None:
                    return repository.create_storage(room, shelf, box)
                raise StorageExceptionBox(message="Box already exists in the database.", code=400)
        except Exception as e:
            raise e

    @staticmethod
    def read_all():
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.read_all()
        except Exception as e:
            raise e

    @staticmethod
    def read_storage_by_id(storage_id: str):
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.read_storage_by_id(storage_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_storage_by_id(storage_id: str):
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.delete_storage(storage_id)
        except Exception as e:
            raise e
