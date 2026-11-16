"""This module defines an SQLAlchemy model for working with specimen data in a database."""


from datetime import date, datetime
from sqlalchemy import Column, String, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base, new_id


class Specimen(Base):
    """SQLAlchemy model for a specimen record in a database."""
    __tablename__ = "specimen"
    specimen_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    reg_no = Column(String(10), unique=True, nullable=False)
    collection_date = Column(Date)
    reg_date = Column(Date, default=datetime.utcnow)
    taxon_id = Column(String(50), ForeignKey("taxonomy.taxon_id"))
    subnomen = Column(String(200))
    field_loc_id = Column(String(50), ForeignKey("field_loc.field_loc_id"))
    storage_id = Column(String(50), ForeignKey("storage.storage_id"))
    collected_by = Column(String(50), ForeignKey("users.user_id"))
    verified_by = Column(String(50), ForeignKey("users.user_id"))

    field_loc = relationship("FieldLoc", back_populates="specimens")
    weather = relationship("Weather", back_populates="specimen", uselist=False, cascade="all, delete")

    def __init__(self, reg_no: str, collection_date: date | str, reg_date: date | str, taxon_id: str,
                 subnomen: str, field_loc_id: str, storage_id: str,
                 collected_by: str, verified_by: str):

        self.reg_no = reg_no
        self.collection_date = date.fromisoformat(collection_date) if isinstance(collection_date, str) else collection_date
        self.reg_date = date.fromisoformat(reg_date) if isinstance(reg_date, str) else reg_date
        self.taxon_id = taxon_id
        self.subnomen = subnomen
        self.field_loc_id = field_loc_id
        self.storage_id = storage_id
        self.collected_by = collected_by
        self.verified_by = verified_by
