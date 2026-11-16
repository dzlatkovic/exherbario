from sqlalchemy import Column, Double, ForeignKey, String

from app.db import Base


class Measurement(Base):
    __tablename__ = "chemistry_measurement"

    profile_id = Column(String(50), ForeignKey("chemistry_profile.id"), primary_key=True)
    feature = Column(String(160), primary_key=True)
    value = Column(Double)
    confidence = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
