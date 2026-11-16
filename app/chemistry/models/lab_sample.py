from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base, new_id


class LabSample(Base):
    __tablename__ = "chemistry_sample"
    __table_args__ = (UniqueConstraint("study_id", "code", name="uq_chemistry_sample_code"),)

    id = Column(String(50), primary_key=True, default=new_id)
    study_id = Column(String(50), ForeignKey("chemistry_study.id"), nullable=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"), nullable=False)
    code = Column(String(80), nullable=False)
    plant_part = Column(String(100), nullable=False)
    collection_event = Column(String(200), nullable=False)
    voucher_relationship = Column(String(30), nullable=False)
