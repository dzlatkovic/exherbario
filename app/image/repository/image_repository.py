from sqlalchemy.orm import Session

from app.db import lock_for_update
from app.image.exceptions import ImageNotFoundException
from app.image.models import Image
from app.image.schemas import ImageSchemaIn
from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.models import Specimen


class ImageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_image(self, image_data: ImageSchemaIn):
        db_image = Image(specimen_id=image_data.specimen_id,
                         image_type=image_data.image_type,
                         file_path=image_data.file_path,
                         width=image_data.width,
                         height=image_data.height,
                         upload_date=image_data.upload_date,
                         sha256=image_data.sha256)
        self.db.add(db_image)
        self.db.flush()
        self.db.refresh(db_image)
        return db_image

    def get_image_by_id(self, image_id: str, for_update: bool = False):
        query = self.db.query(Image).filter_by(image_id=image_id)
        image = (lock_for_update(self.db, query) if for_update else query).first()
        if image is None:
            raise ImageNotFoundException(f"Image with provided ID: "
                                         f"{image_id} not found.", 404)
        return image

    def get_all_images_for_specimen(self, specimen_id: str):
        specimen = self.db.query(Specimen).filter_by(specimen_id=specimen_id).first()
        if not specimen:
            raise SpecimenNotFoundException(
                code=404,
                message=f"Specimen with ID: {specimen_id} does not exist."
            )
        return self.db.query(Image).filter(Image.specimen_id == specimen_id).all()

    def images_sharing_path(self, image):
        query = self.db.query(Image.image_id).filter(
            Image.file_path == image.file_path, Image.image_id != image.image_id
        )
        return lock_for_update(self.db, query).first() is not None
