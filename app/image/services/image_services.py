"""Validate and store specimen photographs."""

from datetime import date
from hashlib import sha256
from io import BytesIO
from logging import getLogger
from pathlib import Path
from uuid import uuid4

from fastapi import UploadFile
from PIL import Image, ImageOps

from app.db import SessionLocal
from app.file_storage import store_upload
from app.image.exceptions import (
    ImageInUseException,
    ImageNotFoundException,
    InvalidImageFileException,
    InvalidImageFormatException,
    MaximumDimensionsExceededException,
)
from app.image.repository import ImageRepository
from app.image.schemas import ImageSchema, ImageSchemaIn, ImageType
from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.models import Specimen

IMAGE_ROOT = Path("images")
MAX_IMAGE_BYTES = 10 * 1024 * 1024
logger = getLogger(__name__)


class ImageService:
    @staticmethod
    def storage_path(stored_path: str) -> Path:
        path = Path(stored_path).resolve()
        if IMAGE_ROOT.resolve() not in path.parents:
            raise InvalidImageFileException("Image path is outside the storage directory.", 400)
        return path

    @staticmethod
    def public_jpeg(stored_path: str) -> bytes:
        """Render a metadata-free copy without modifying the archived original."""
        try:
            path = ImageService.storage_path(stored_path)
            with path.open("rb") as original:
                data = original.read(MAX_IMAGE_BYTES + 1)
            if len(data) > MAX_IMAGE_BYTES:
                raise InvalidImageFileException("Image exceeds the public size limit.", 400)
            with Image.open(BytesIO(data)) as source:
                if source.format != "JPEG" or max(source.size) > 2048:
                    raise InvalidImageFileException("Unsupported public image.", 400)
                oriented = ImageOps.exif_transpose(source).convert("RGB")
                clean = Image.frombytes("RGB", oriented.size, oriented.tobytes())
                output = BytesIO()
                clean.save(output, format="JPEG", quality=90)
                return output.getvalue()
        except (OSError, ValueError, SyntaxError, Image.DecompressionBombError) as error:
            raise InvalidImageFileException("Invalid JPEG image.", 400) from error

    @staticmethod
    def create_image(specimen_id: str, image_type: ImageType, file: UploadFile):
        image_data = file.file.read(MAX_IMAGE_BYTES + 1)
        if len(image_data) > MAX_IMAGE_BYTES:
            raise InvalidImageFileException("Image exceeds the 10 MiB limit.", 413)

        try:
            with Image.open(BytesIO(image_data)) as image:
                if image.format != "JPEG":
                    raise InvalidImageFormatException("Only JPEG images are supported.", 400)
                width, height = image.size
                if max(width, height) > 2048:
                    raise MaximumDimensionsExceededException(
                        "Image dimensions must not exceed 2048 pixels.", 400
                    )
                image.load()
        except (OSError, Image.DecompressionBombError) as error:
            raise InvalidImageFileException("Invalid JPEG image.", 400) from error

        stored_path = IMAGE_ROOT / f"{uuid4().hex}.jpg"
        path = ImageService.storage_path(str(stored_path))
        with SessionLocal() as db:
            if db.get(Specimen, specimen_id) is None:
                raise SpecimenNotFoundException("Specimen was not found.", 404)
            image_input = ImageSchemaIn(
                specimen_id=specimen_id, image_type=image_type, file_path=stored_path.as_posix(),
                width=width, height=height, upload_date=date.today(),
                sha256=sha256(image_data).hexdigest(),
            )
            record = ImageRepository(db).create_image(image_input)
            response = ImageSchema.from_orm(record)
            with store_upload(path, image_data):
                db.commit()
            return response

    @staticmethod
    def get_image_by_id(image_id):
        with SessionLocal() as db:
            return ImageRepository(db).get_image_by_id(image_id)

    @staticmethod
    def get_all_images_for_specimen(specimen_id: str):
        with SessionLocal() as db:
            images = ImageRepository(db).get_all_images_for_specimen(specimen_id)
            if not images:
                raise ImageNotFoundException("No images were found for this specimen.", 404)
            return images

    @staticmethod
    def delete_image(image_id: str):
        with SessionLocal() as db:
            repository = ImageRepository(db)
            image = repository.get_image_by_id(image_id, for_update=True)
            if image.plantnet_results:
                raise ImageInUseException("Remove linked identification results before deleting this image.", 409)
            path = ImageService.storage_path(image.file_path)
            shared = repository.images_sharing_path(image)
            db.delete(image)
            db.commit()

        if not shared:
            try:
                path.unlink(missing_ok=True)
            except OSError:
                logger.exception("Could not remove unreferenced image %s", path)
        return True
