from datetime import datetime, date
from sqlalchemy import Boolean, Column, String, ForeignKey, Date, Integer, Enum, false
from sqlalchemy.orm import relationship

from app.image.schemas import ImageType
from app.db import Base, new_id


class Image(Base):
    __tablename__ = "image"
    image_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    image_type = Column(Enum(ImageType))
    file_path = Column(String(150))
    width = Column(Integer)
    height = Column(Integer)
    upload_date = Column(Date, default=datetime.utcnow)
    is_public = Column(Boolean, nullable=False, server_default=false())
    ever_public = Column(Boolean, nullable=False, server_default=false())
    sha256 = Column(String(64))

    plantnet_results = relationship("PlantNetResult", backref="image")

    def __init__(self,
                 specimen_id: str,
                 image_type: ImageType,
                 file_path: str,
                 width: int,
                 height: int,
                 upload_date: date,
                 sha256: str | None = None,
                 ):
        self.specimen_id = specimen_id
        self.image_type = image_type
        self.file_path = file_path
        self.width = width
        self.height = height
        self.upload_date = upload_date
        self.sha256 = sha256
