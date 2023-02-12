from sqlalchemy import Column, String
from uuid import uuid4

from app.db import Base


class Photos(Base):
    __tablename__ = "photos"
    photos_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    field_photo = Column(String(200))
    specimen_photo = Column(String(200))

    def __init__(self, field_photo: str, specimen_photo: str):
        self.field_photo = field_photo
        self.specimen_photo = specimen_photo
