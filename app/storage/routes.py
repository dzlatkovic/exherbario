"""
This module defines an API router for a storage system.
"""

from fastapi import APIRouter, Depends

from app.storage.controller import StorageController
from app.storage.schemas import StorageSchema, StorageSchemaIn, StorageSchemaUpdate
from app.users.controller.user_auth_controller import JWTBearer

storage_router = APIRouter(prefix="/api/storage", tags=["Storage"])


@storage_router.post("/create-new-storage", response_model=StorageSchema,
                     dependencies=[Depends(JWTBearer("super_user"))])
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


@storage_router.delete("/delete-storage", dependencies=[Depends(JWTBearer("super_user"))])
def delete_storage_by_id(storage_id: str):
    """
    Delete a storage object by its ID
    :param storage_id: The ID of the storage object to delete
    """
    return StorageController.delete_storage_by_id(storage_id)


@storage_router.get("/get-box-content")
def get_box_content(box: str):
    """
    This function returns the content of a box
    :param box: The name of the box you want to get the content of
    :type box: str
    :return: A list of the contents of the box.
    """
    return StorageController.get_box_content(box)


@storage_router.put("/update-storage", response_model=StorageSchema,
                    dependencies=[Depends(JWTBearer("super_user"))])
def update_storage(storage_id: str, storage_data: StorageSchemaUpdate):
    """
    Update an existing storage with the given data.

    This endpoint updates an existing storage with the given ID using the provided data.
    The storage's `room` and `shelf` attributes can be updated with this endpoint

    :param storage_id: The ID of the storage to update.
    :type storage_id: str
    :param storage_data: The data to update the storage with.
    :type storage_data: StorageSchemaUpdate.
    :return: The updated storage object.
    """
    return StorageController.update_storage(storage_id, storage_data)
