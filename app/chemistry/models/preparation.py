from sqlalchemy import Column, Double, ForeignKey, String, UniqueConstraint

from app.db import Base, new_id


class Preparation(Base):
    __tablename__ = "chemistry_preparation"
    __table_args__ = (UniqueConstraint("sample_id", "batch_code", name="uq_chemistry_batch_code"),)

    id = Column(String(50), primary_key=True, default=new_id)
    sample_id = Column(String(50), ForeignKey("chemistry_sample.id"), nullable=False)
    batch_code = Column(String(80), nullable=False)
    kind = Column(String(20), nullable=False)
    method_reference = Column(String(500), nullable=False)
    plant_material_mass_g = Column(Double)
    method_parameters = Column(String(1000))
    yield_percent = Column(Double)  # % w/w
