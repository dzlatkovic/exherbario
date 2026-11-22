from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base, new_id


class SpreadsheetImport(Base):
    """An author's results table being turned into profiles. Nothing becomes a profile until it is confirmed."""
    __tablename__ = "chemistry_import"

    id = Column(String(50), primary_key=True, default=new_id)
    study_id = Column(String(50), ForeignKey("chemistry_study.id"), nullable=False)
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    status = Column(String(20), nullable=False)  # draft or confirmed
    created_at = Column(DateTime, nullable=False)
    confirmed_at = Column(DateTime)
    source_name = Column(String(200), nullable=False)
    source_kind = Column(String(10), nullable=False)  # xlsx or csv
    source_path = Column(String(150), nullable=False)
    source_sha256 = Column(String(64), nullable=False)
    assignment = Column(JSON)
    review = Column(JSON)


class ImportTemplate(Base):
    """A saved column assignment, so a table with the same layout imports in one step."""
    __tablename__ = "chemistry_import_template"
    __table_args__ = (UniqueConstraint("owner_id", "name", name="uq_chemistry_import_template_name"),)

    id = Column(String(50), primary_key=True, default=new_id)
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    name = Column(String(120), nullable=False)
    layout = Column(JSON, nullable=False)
    created_at = Column(DateTime, nullable=False)


class ConditionPreset(Base):
    """Run conditions or a preparation method an author saved by name; applying one fills in the form."""
    __tablename__ = "chemistry_condition_preset"
    __table_args__ = (UniqueConstraint("owner_id", "kind", "name", name="uq_chemistry_condition_preset_name"),)

    id = Column(String(50), primary_key=True, default=new_id)
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    kind = Column(String(20), nullable=False)  # run or preparation
    name = Column(String(120), nullable=False)
    values = Column(JSON, nullable=False)
    updated_at = Column(DateTime, nullable=False)
