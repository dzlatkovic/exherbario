"""
This module contains the business logic for storage operations.
"""


from app.storage.models import Storage
from app.db import SessionLocal
from app.storage.repository import StorageRepository
from app.storage.exceptions import StorageExceptionBox
from app.storage.schemas import StorageSchemaUpdate
from app.storage.exceptions import StorageNotFoundException


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

    @staticmethod
    def get_box_content(box: str):
        """
        It gets the content of a box
        :param box: The name of the box you want to get the content of
        :type box: str
        :return: A list of dictionaries.
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                return repository.get_box_content(box)
        except Exception as error:
            raise error

    @staticmethod
    def update_storage(storage_id: str, storage_data: StorageSchemaUpdate):
        """
        It updates a storage in the database

        :param storage_id: The id of the storage to be updated
        :type storage_id: str
        :param storage_data: StorageSchemaUpdate
        :type storage_data: StorageSchemaUpdate
        :return: The updated storage object.
        """
        try:
            with SessionLocal() as db:
                repository = StorageRepository(db)
                db_storage = repository.update_storage(storage_id, storage_data)
                if db_storage is None:
                    raise StorageNotFoundException(message="Storage was not found.", code=400)
                return db_storage
        except Exception as error:
            raise error
