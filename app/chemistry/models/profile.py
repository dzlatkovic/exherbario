from sqlalchemy import Boolean, Column, ForeignKey, String, Text, UniqueConstraint
from sqlalchemy.dialects.mysql import MEDIUMTEXT
from sqlalchemy.orm import deferred

from app.db import Base, new_id


class Profile(Base):
    __tablename__ = "chemistry_profile"
    __table_args__ = (UniqueConstraint("preparation_id", "run_code", name="uq_chemistry_run_code"),)

    id = Column(String(50), primary_key=True, default=new_id)
    preparation_id = Column(String(50), ForeignKey("chemistry_preparation.id"), nullable=False)
    run_code = Column(String(80), nullable=False)
    analytical_method = Column(String(120), nullable=False)
    measurement_basis = Column(String(25), nullable=False)
    unit = Column(String(40), nullable=False)
    source_name = Column(String(200), nullable=False)
    source_csv = deferred(Column(Text().with_variant(MEDIUMTEXT(), "mysql"), nullable=False))
    is_public = Column(Boolean, nullable=False, default=False)
