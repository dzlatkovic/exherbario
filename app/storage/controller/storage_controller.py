from app.storage.services import StorageService
from app.storage.exceptions import StorageExceptionBox, StorageNotFoundException

from fastapi import HTTPException, Response


class StorageController:

    @staticmethod
    def create_new_storage(room: str, shelf: str, box: str):
        try:
            return StorageService.create_new_storage(room, shelf, box)
        except StorageExceptionBox as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_all():
        return StorageService.read_all()

    @staticmethod
    def get_storage_by_id(storage_id: str):
        try:
            return StorageService.read_storage_by_id(storage_id)
        except StorageNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_storage_by_id(storage_id: str):
        try:
            StorageService.delete_storage_by_id(storage_id)
            return Response(content=f"Box with the provided ID: {storage_id} deleted.", status_code=200)
        except StorageNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
