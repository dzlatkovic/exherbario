"""This module defines an SQLAlchemy model for working with specimen data in a database."""


from uuid import uuid4
from datetime import datetime
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base


class Specimen(Base):
    """SQLAlchemy model for a specimen record in a database."""
    __tablename__ = "specimen"
    specimen_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    reg_no = Column(String(10), unique=True, nullable=False)
    collection_date = Column(Date)
    reg_date = Column(Date, default=datetime.utcnow)
    family = Column(String(50))
    genus = Column(String(50))
    species = Column(String(50))
    subnomen = Column(String(200))
    field_loc_id = Column(String(50), ForeignKey("field_loc.field_loc_id"))
    storage_id = Column(String(50), ForeignKey("storage.storage_id"))
    photos_id = Column(String(50), ForeignKey("photos.photos_id"), unique=True)
    collected_by = Column(String(50), ForeignKey("users.user_id"))
    verified_by = Column(String(50), ForeignKey("users.user_id"))

    field_loc = relationship("FieldLoc", back_populates="specimens")
    weather = relationship("Weather", back_populates="specimen", uselist=False, cascade="all, delete")

    def __init__(self, reg_no: str, collection_date: str, reg_date: str,
                 family: str, genus: str, species: str, subnomen: str,
                 field_loc_id: str, storage_id: str, photos_id: str,
                 collected_by: str, verified_by: str):

        """Create a new `Specimen` object
        This method creates a new `Specimen` object with the specified field values. It sets the
        `reg_no`, `collection_date`, `reg_date`, `family`, `genus`, `species`, `subnomen`,
        `field_loc_id`, `storage_id`, `photos_id`, `collected_by`, and `verified_by` fields
        according to the corresponding arguments
        :param reg_no: The registration number for the specimen record
        :type reg_no: str
        :param collection_date: The date the specimen was collected, in "yyyy-mm-dd" format.
        :type collection_date: str
        :param reg_date: The date the specimen was registered, in "yyyy-mm-dd" format.
        :type reg_date: str
        :param family: The family of the specimen
        :type family: str
        :param genus: The genus of the specimen
        :type genus: str
        :param species: The species of the specimen
        :type species: str
        :param subnomen: The subnomen of the specimen
        :type subnomen: str
        :param field_loc_id: The ID of the field location where the specimen was collected
        :type field_loc_id: str
        :param storage_id: The ID of the storage location where the specimen is stored
        :type storage_id: str
        :param photos_id: The ID of the photos associated with the specimen
        :type photos_id: str
        :param collected_by: The ID of the user who collected the specimen
        :type collected_by: str
        :param verified_by: The ID of the user who verified the specimen
        :type verified_by: str
        """
        self.reg_no = reg_no
        self.collection_date = datetime.strptime(collection_date, "%Y-%m-%d")
        self.reg_date = datetime.strptime(reg_date, "%Y-%m-%d")
        self.family = family
        self.genus = genus
        self.species = species
        self.subnomen = subnomen
        self.field_loc_id = field_loc_id
        self.storage_id = storage_id
        self.photos_id = photos_id
        self.collected_by = collected_by
        self.verified_by = verified_by
