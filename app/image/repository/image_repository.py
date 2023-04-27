from sqlalchemy.orm import Session
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
                         upload_date=image_data.upload_date)
        self.db.add(db_image)
        self.db.commit()
        self.db.refresh(db_image)
        return db_image

    def get_image_by_id(self, image_id: str):
        image = self.db.query(Image).filter(Image.image_id == image_id).first()
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

    def delete_image_data(self, image_id: str):
        try:
            image_db = self.get_image_by_id(image_id)
            self.db.delete(image_db)
            self.db.commit()
            return True
        except Exception as error:
            raise error
