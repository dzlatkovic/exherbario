from sqlalchemy import Column, Date, ForeignKey, String, UniqueConstraint

from app.db import Base, new_id


class LabSample(Base):
    __tablename__ = "chemistry_sample"
    __table_args__ = (UniqueConstraint("study_id", "code", name="uq_chemistry_sample_code"),)

    id = Column(String(50), primary_key=True, default=new_id)
    study_id = Column(String(50), ForeignKey("chemistry_study.id"), nullable=False)
    code = Column(String(80), nullable=False)
    plant_part = Column(String(100), nullable=False)
    plant_part_note = Column(String(200))
    # Unrecorded (NULL) only for samples created before structured provenance.
    material_state = Column(String(20))
    collection_date = Column(Date)
    phenological_stage = Column(String(100))
    # The collection site is either a linked voucher's site or the sample's own field location.
    site_specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    field_loc_id = Column(String(50), ForeignKey("field_loc.field_loc_id"))
    drying_notes = Column(String(1000))
    storage_notes = Column(String(1000))
    # Private free-text notes, including the former collection event description.
    collection_notes = Column(String(200))
