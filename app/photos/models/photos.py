"""This module defines the Photos model"""


from uuid import uuid4

from sqlalchemy import Column, String, CheckConstraint

from app.db import Base


class Photos(Base):
    """The photos table in the database"""
    __tablename__ = "photos"
    photos_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    field_photo = Column(String(200), unique=True)
    specimen_photo = Column(String(200), unique=True)

    __table_args__ = (
        CheckConstraint("field_photo <> specimen_photo"),
    )

    def __init__(self, field_photo: str, specimen_photo: str):
        """
        Initializes a new instance of the Photos model
        :param field_photo: The path to the field photo
        :type field_photo: str
        :param specimen_photo: The path to the specimen photo
        :type specimen_photo: str
        """
        self.field_photo = field_photo
        self.specimen_photo = specimen_photo
