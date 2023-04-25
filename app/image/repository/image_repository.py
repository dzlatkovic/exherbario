from sqlalchemy.orm import Session
from app.image.models import Image
from app.image.schemas import ImageSchemaIn


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
