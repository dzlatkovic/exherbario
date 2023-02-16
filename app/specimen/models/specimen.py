from datetime import datetime
from sqlalchemy import Column, String, Date, ForeignKey
from uuid import uuid4

from app.db import Base


class Specimen(Base):
    __tablename__ = "specimen"
    specimen_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    reg_no = Column(String(10), unique=True)
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

    def __init__(self, reg_no: str, collection_date: str, reg_date: str,
                 family: str, genus: str, species: str, subnomen: str,
                 field_loc_id: str, storage_id: str, photos_id: str,
                 collected_by: str, verified_by: str):
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
