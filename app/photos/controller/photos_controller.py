from app.photos.services import PhotosService
from app.photos.exceptions import PhotosNotFoundException

from fastapi import HTTPException, Response


class PhotosController:

    @staticmethod
    def create_new_photos(field_photo: str, specimen_photo: str):
        try:
            photos = PhotosService.create_new_photos(field_photo, specimen_photo)
            return photos
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_all_photos():
        photos = PhotosService.read_all_photos()
        return photos

    @staticmethod
    def get_photos_by_id(photos_id: str):
        try:
            photos = PhotosService.read_photos_by_id(photos_id)
            return photos
        except PhotosNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_photos_by_id(photos_id: str):
        try:
            PhotosService.delete_photos_by_id(photos_id)
            return Response(content=f"Photos with provided ID: "
                                    f"{photos_id} deleted.", status_code=200)
        except PhotosNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
