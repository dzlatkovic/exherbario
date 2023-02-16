"""
This module defines an API router for a storage system.
"""


from fastapi import APIRouter

from app.storage.controller import StorageController
from app.storage.schemas import StorageSchema, StorageSchemaIn

storage_router = APIRouter(prefix="/api/storage", tags=["Storage"])


@storage_router.post("/create-new-storage", response_model=StorageSchema)
def create_new_storage(storage: StorageSchemaIn):
    """
    Create a new storage object
    :param storage: A `StorageSchemaIn` object containing the room, shelf, and box values
    :return: A `StorageSchema` object representing the newly created storage object.
    """
    return StorageController.create_new_storage(room=storage.room, shelf=storage.shelf,
                                                box=storage.box)


@storage_router.get("/get-all", response_model=list[StorageSchema])
def get_all():
    """
    Retrieve a list of all storage objects
    :return: A list of `StorageSchema` objects, all the storage objects in the database.
    """
    return StorageController.get_all()


@storage_router.get("/get-storage-by-id", response_model=StorageSchema)
def get_storage_by_id(storage_id: str):
    """
    Retrieve a storage object by its ID
    :param storage_id: The ID of the storage object to retrieve
    :return: A `StorageSchema` object representing the storage object with the specified ID
    """
    return StorageController.get_storage_by_id(storage_id)


@storage_router.delete("/delete-storage")
def delete_storage_by_id(storage_id: str):
    """
    Delete a storage object by its ID
    :param storage_id: The ID of the storage object to delete
    """
    return StorageController.delete_storage_by_id(storage_id)
