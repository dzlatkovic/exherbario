from sqlalchemy import Column, Double, ForeignKey, Integer, String

from app.db import Base


class Measurement(Base):
    __tablename__ = "chemistry_measurement"

    profile_id = Column(String(50), ForeignKey("chemistry_profile.id"), primary_key=True)
    feature = Column(String(160), primary_key=True)
    value = Column(Double)
    confidence = Column(String(30), nullable=False)
    status = Column(String(20), nullable=False)
    # Identification evidence. All optional; technique-specific fields are checked at import.
    cid = Column(Integer, ForeignKey("compound.cid"))
    compound_match = Column(String(30))
    rt_min = Column(Double)
    id_basis = Column(String(60))
    id_level = Column(Integer)
    qualifier = Column(String(10))
    sd = Column(Double)
    n = Column(Integer)
    ri_exp = Column(Double)
    ri_ref = Column(Double)
    ri_ref_source = Column(String(200))
    ri_ref_polarity = Column(String(12))
    library_match = Column(String(200))
    library_score = Column(Double)
    mz_obs = Column(Double)
    adduct = Column(String(40))
    mass_error_ppm = Column(Double)
    msms_match = Column(String(200))
