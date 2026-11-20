from sqlalchemy import JSON, Boolean, Column, ForeignKey, String, Text, UniqueConstraint
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
    source_csv = deferred(Column(Text, nullable=False))
    source_path = Column(String(150))
    source_sha256 = Column(String(64))
    is_public = Column(Boolean, nullable=False, default=False)
    # Required for new profiles; NULL for profiles imported before techniques were recorded.
    technique = Column(String(20))
    run_metadata = Column(JSON)
    # Set for profiles created from a spreadsheet import: the import and the source column header.
    import_id = Column(String(50), ForeignKey("chemistry_import.id"))
    import_column = Column(String(200))

    @property
    def source_fidelity(self):
        return "byte-preserved" if self.source_path else "legacy-reconstructed"
