from fastapi import APIRouter

from app.storage.controller import StorageController
from app.storage.schemas import StorageSchema, StorageSchemaIn

storage_router = APIRouter(prefix="/api/storage", tags=["Storage"])


@storage_router.post("/create-new-storage", response_model=StorageSchema)
def create_new_course(storage: StorageSchemaIn):
    return StorageController.create_new_storage(room=storage.room, shelf=storage.shelf,
                                                box=storage.box)


@storage_router.get("/get-all", response_model=list[StorageSchema])
def get_all():
    return StorageController.get_all()


@storage_router.get("/get-storage-by-id", response_model=StorageSchema)
def get_storage_by_id(storage_id: str):
    return StorageController.get_storage_by_id(storage_id)


@storage_router.delete("/delete-storage")
def delete_storage_by_id(storage_id: str):
    return StorageController.delete_storage_by_id(storage_id)
