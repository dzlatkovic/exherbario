import os
from datetime import datetime

from fastapi import UploadFile
from app.db import SessionLocal
from app.image.repository import ImageRepository
from app.image.schemas import ImageSchemaIn, ImageType
from PIL import Image
from app.image.exceptions import (InvalidImageFileException,
                                  InvalidImageFormatException,
                                  MaximumDimensionsExceededException,
                                  ImageNotFoundException,
                                  MissingFileException)


class ImageService:
    @staticmethod
    def get_image_data(file: UploadFile):
        try:
            img = Image.open(file.file)
        except Exception:
            raise InvalidImageFileException(code=400,
                                            message="Invalid image file.")
        if img.format not in ['JPEG', 'JPG']:
            raise InvalidImageFormatException(
                code=400,
                message="Invalid image format. Only JPEG and JPG are supported.")
        width, height = img.size
        if max(width, height) > 2048:
            raise MaximumDimensionsExceededException(
                code=400,
                message="Image dimensions should not exceed 2048 pixels."
            )
        return file.filename, width, height

    @staticmethod
    def create_image(specimen_id: str, image_type: ImageType, file: UploadFile):
        # Read the image data from the upload file
        image_data = file.file.read()

        # Get the filename, file path, and metadata for the image
        file_name, width, height = ImageService.get_image_data(file)
        # Create a Pydantic model for the image
        image = ImageSchemaIn(
            specimen_id=specimen_id,
            image_type=image_type,
            file_path=f"images/{specimen_id}/{file_name}",
            width=width,
            height=height,
            upload_date=datetime.now()
        )
        # Use the ImageRepository to save the image data to the database
        with SessionLocal() as db:
            repository = ImageRepository(db)
            db_image = repository.create_image(image)

            # Write the image data to disk
            if not os.path.exists(f'images/{specimen_id}'):
                os.makedirs(f'images/{specimen_id}')
            with open(f"images/{specimen_id}/{file.filename}", "wb") as f:
                f.write(image_data)

            # Return the database model for the saved image
            return db_image

    @staticmethod
    def get_image_by_id(image_id):
        try:
            with SessionLocal() as db:
                repository = ImageRepository(db)
                return repository.get_image_by_id(image_id)
        except Exception as error:
            raise error

    @staticmethod
    def get_all_images_for_specimen(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = ImageRepository(db)
                images = repository.get_all_images_for_specimen(specimen_id)
                if not images:
                    raise ImageNotFoundException(
                        code=404,
                        message=f"No images were found for specimen with ID: {specimen_id}"
                    )
                return images
        except Exception as error:
            raise error

    @staticmethod
    def delete_image_file(image_path: str) -> None:
        if not os.path.exists(image_path):
            raise MissingFileException(
                code=400,
                message="The image file is missing. Database entry is successfully deleted."
            )
        os.remove(image_path)

    @staticmethod
    def delete_image(image_id: str):
        try:
            with SessionLocal() as db:
                repository = ImageRepository(db)
                image = ImageService.get_image_by_id(image_id)
                flag = repository.delete_image_data(image_id)
                ImageService.delete_image_file(image.file_path)
                return flag
        except MissingFileException as error:
            raise error
        except Exception as error:
            raise error
