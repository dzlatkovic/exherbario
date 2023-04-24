from datetime import datetime, date
from uuid import uuid4

from sqlalchemy import Column, String, ForeignKey, Date, JSON, Integer

from app.db import Base


class Image(Base):
    __tablename__ = "image"
    image_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    file_path = Column(String(150))
    width = Column(Integer)
    height = Column(Integer)
    upload_date = Column(Date, default=datetime.utcnow)

    def __init__(self,
                 specimen_id: str,
                 file_path: str,
                 width: int,
                 height: int,
                 upload_date: date
                 ):
        self.specimen_id = specimen_id
        self.file_path = file_path
        self.width = width
        self.height = height
        self.upload_date = upload_date
