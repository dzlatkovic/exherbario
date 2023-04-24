import json
import os
from datetime import datetime

from fastapi import UploadFile
from app.db import SessionLocal
from app.image.repository import ImageRepository
from app.image.schemas import ImageSchemaIn
from PIL import Image


class ImageService:
    @staticmethod
    def get_image_data(file: UploadFile):
        file_path = f"images/{file.filename}"
        img = Image.open(file.file)
        width, height = img.size
        return file_path, width, height

    @staticmethod
    def create_image(specimen_id: str, file: UploadFile):
        # Read the image data from the upload file
        image_data = file.file.read()

        # Get the filename, file path, and metadata for the image
        file_path, width, height = ImageService.get_image_data(file)
        # Create a Pydantic model for the image
        image = ImageSchemaIn(
            specimen_id=specimen_id,
            file_path=file_path,
            width=width,
            height=height,
            upload_date=datetime.now()
        )
        # Use the ImageRepository to save the image data to the database
        with SessionLocal() as db:
            repository = ImageRepository(db)
            db_image = repository.create_image(image)

            # Write the image data to disk
            if not os.path.exists('images'):
                os.makedirs('images')
            with open(f"images/{file.filename}", "wb") as f:
                f.write(image_data)

            # Return the database model for the saved image
            return db_image
