"""
This module contains the business logic for storage operations.
"""


from app.storage.models import Storage
from app.db import SessionLocal
from app.storage.repository import StorageRepository
from app.storage.exceptions import StorageExceptionBox


class StorageService:
    """
    This class implements the business logic for the storage box
    related API endpoints.
    """
    @staticmethod
    def create_new_storage(room: str, shelf: str, box: str) -> StorageExceptionBox or Storage:
        """
        Creates a new storage box and stores it in the database
        :param room: The name of the room where the storage box is located
        :param shelf: The name of the shelf where the storage box is located
        :param box: The name of the storage box
        :return: The newly created storage box
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                storage = repository.read_storage_by_box(box)
                if storage is None:
                    return repository.create_storage(room, shelf, box)
                raise StorageExceptionBox(message="Box already exists in the database.", code=400)
        except Exception as error:
            raise error

    @staticmethod
    def read_all():
        """
        Returns all storage boxes
        :return: List of all storage boxes
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.read_all()
        except Exception as error:
            raise error

    @staticmethod
    def read_storage_by_id(storage_id: str):
        """
        Returns a storage box by ID
        :param storage_id: The ID of the storage box to return
        :return: The storage box with the provided ID
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.read_storage_by_id(storage_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_storage_by_id(storage_id: str):
        """
        Deletes a storage box by ID
        :param storage_id: The ID of the storage box to delete
        :return: Boolean indicating whether the deletion was successful
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.delete_storage(storage_id)
        except Exception as error:
            raise error
