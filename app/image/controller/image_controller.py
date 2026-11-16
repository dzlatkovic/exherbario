from fastapi import HTTPException, UploadFile, Response
from app.image.exceptions import (InvalidImageFileException,
                                  InvalidImageFormatException,
                                  MaximumDimensionsExceededException,
                                  ImageInUseException, ImageNotFoundException)
from app.image.schemas import ImageType

from app.image.services import ImageService
from app.specimen.exceptions import SpecimenNotFoundException


class ImageController:
    @staticmethod
    def create_image(specimen_id: str, image_type: ImageType, file: UploadFile):
        try:
            return ImageService.create_image(specimen_id, image_type, file)
        except (InvalidImageFileException,
                InvalidImageFormatException,
                MaximumDimensionsExceededException, SpecimenNotFoundException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_image_by_id(image_id):
        try:
            return ImageService.get_image_by_id(image_id)
        except ImageNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_all_images_for_specimen(specimen_id: str):
        try:
            return ImageService.get_all_images_for_specimen(specimen_id)
        except (ImageNotFoundException, SpecimenNotFoundException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_image(image_id: str):
        try:
            ImageService.delete_image(image_id)
            return Response(content="Image record deleted.",
                            status_code=200)
        except (ImageInUseException, ImageNotFoundException, InvalidImageFileException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
