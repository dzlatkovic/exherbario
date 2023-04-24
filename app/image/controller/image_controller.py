from fastapi import HTTPException, UploadFile, File

from app.image.services import ImageService


class ImageController:
    @staticmethod
    def create_image(specimen_id: str, file: UploadFile):
        try:
            return ImageService.create_image(specimen_id, file)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
