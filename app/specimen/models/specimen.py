"""This module defines an SQLAlchemy model for working with specimen data in a database."""


from datetime import date, datetime
from sqlalchemy import Boolean, Column, String, Date, ForeignKey, Text, UniqueConstraint, false
from sqlalchemy.orm import relationship

from app.db import Base, new_id


class Specimen(Base):
    """SQLAlchemy model for a specimen record in a database."""
    __tablename__ = "specimen"
    __table_args__ = (UniqueConstraint(
        "holding_institution", "collection", "accession", name="uq_specimen_holding_accession",
    ),)
    specimen_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    reg_no = Column(String(40), unique=True)
    collection_date = Column(Date)
    reg_date = Column(Date, default=datetime.utcnow)
    taxon_id = Column(String(50), ForeignKey("taxonomy.taxon_id"))
    subnomen = Column(String(200))
    field_loc_id = Column(String(50), ForeignKey("field_loc.field_loc_id"))
    storage_id = Column(String(50), ForeignKey("storage.storage_id"))
    collected_by = Column(String(50), ForeignKey("users.user_id"))
    verified_by = Column(String(50), ForeignKey("users.user_id"))
    is_public = Column(Boolean, nullable=False, server_default=false())
    ever_public = Column(Boolean, nullable=False, server_default=false())
    public_location = Column(String(8), nullable=False, server_default="withheld")
    holding_type = Column(String(8))
    holding_institution = Column(String(120))
    collection = Column(String(120))
    accession = Column(String(100))
    verbatim_label = Column(Text)
    collector_name = Column(String(200))
    collector_number = Column(String(100))
    verbatim_collection_date = Column(String(100))
    type_status = Column(String(50))
    verifier_name = Column(String(200))
    determiner_name = Column(String(200))
    determination_date = Column(Date)

    field_loc = relationship("FieldLoc", back_populates="specimens")
    weather = relationship("Weather", back_populates="specimen", uselist=False, passive_deletes="all")

    def __init__(self, reg_no=None, collection_date=None, reg_date=None, taxon_id=None,
                 subnomen=None, field_loc_id=None, storage_id=None, collected_by=None, verified_by=None,
                 **metadata):
        super().__init__(
            reg_no=reg_no, taxon_id=taxon_id, subnomen=subnomen, field_loc_id=field_loc_id,
            storage_id=storage_id, collected_by=collected_by, verified_by=verified_by,
            collection_date=date.fromisoformat(collection_date) if isinstance(collection_date, str) else collection_date,
            reg_date=date.fromisoformat(reg_date) if isinstance(reg_date, str) else reg_date,
            **metadata,
        )
