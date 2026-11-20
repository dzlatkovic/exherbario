from sqlalchemy import Column, Date, DateTime, ForeignKey, String

from app.db import Base


class SampleVoucher(Base):
    """A voucher linked to a lab sample, with the voucher's determination when the link was made."""
    __tablename__ = "chemistry_sample_voucher"

    sample_id = Column(String(50), ForeignKey("chemistry_sample.id"), primary_key=True)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"), primary_key=True)
    role = Column(String(40), nullable=False)
    linked_at = Column(DateTime, nullable=False)
    taxon_id_at_link = Column(String(50))
    taxon_name_at_link = Column(String(255))
    name_at_link = Column(String(200))
    determination_date_at_link = Column(Date)
    # "at_link" when recorded on linking; "at_migration" for links converted by migration 0010.
    determination_recorded = Column(String(20), nullable=False)
