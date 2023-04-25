from fastapi import HTTPException, UploadFile
from app.image.exceptions import InvalidImageFileException, InvalidImageFormatException
from app.image.schemas import ImageType

from app.image.services import ImageService


class ImageController:
    @staticmethod
    def create_image(specimen_id: str, image_type: ImageType, file: UploadFile):
        try:
            return ImageService.create_image(specimen_id, image_type, file)
        except (InvalidImageFileException, InvalidImageFormatException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
