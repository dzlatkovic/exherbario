"""
This module contains the controllers for the storage API endpoints. These controllers
handle incoming requests from clients and call the appropriate services to perform the
necessary actions on the storage data.
"""


from fastapi import HTTPException, Response

from app.storage.services import StorageService
from app.storage.exceptions import StorageExceptionBox, StorageNotFoundException


class StorageController:
    """
    Controller class for the storage objects.
    """
    @staticmethod
    def create_new_storage(room: str, shelf: str, box: str):
        """
        Create a new storage object with the specified room, shelf, and box values
        :param room: The room in which the specimen is located
        :param shelf: The shelf on which the specimen is located
        :param box: The box in which the specimen is located
        :return: The new storage object created by the service
        """
        try:
            return StorageService.create_new_storage(room, shelf, box)
        except StorageExceptionBox as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_all():
        """
        Retrieve a list of all storage objects in the database
        :return: A list of all storage objects in the database
        """
        return StorageService.read_all()

    @staticmethod
    def get_storage_by_id(storage_id: str):
        """
        Retrieve the storage object with the specified ID
        :param storage_id: The ID of the storage object to retrieve
        :return: The storage object with the specified ID
        """
        try:
            return StorageService.read_storage_by_id(storage_id)
        except StorageNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_storage_by_id(storage_id: str):
        """
        Delete the storage object with the specified ID
        :param storage_id: The ID of the storage object to delete
        :return: A Response object indicating success or failure
        """
        try:
            StorageService.delete_storage_by_id(storage_id)
            return Response(content=f"Box with the provided ID: {storage_id} deleted.",
                            status_code=200)
        except StorageNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
