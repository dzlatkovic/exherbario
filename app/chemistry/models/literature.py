"""Natural products reported in the literature for a taxon, shown publicly only after a curator confirms them."""

from sqlalchemy import JSON, Column, DateTime, ForeignKey, Integer, String, UniqueConstraint

from app.db import Base, new_id


class TaxonLiteratureCompound(Base):
    """One compound LOTUS (via Wikidata) reports for a taxon, as published by a curator. This is a copy of the
    provider's answer at `retrieved_at`, not a measurement; refreshing replaces the taxon's rows."""
    __tablename__ = "taxon_literature_compound"
    __table_args__ = (UniqueConstraint("taxon_id", "wikidata_id", name="uq_taxon_literature_compound"),)

    id = Column(String(50), primary_key=True, default=new_id)
    taxon_id = Column(String(50), ForeignKey("taxonomy.taxon_id"), nullable=False, index=True)
    wikidata_id = Column(String(20), nullable=False)
    name = Column(String(500), nullable=False)
    inchikey = Column(String(27))
    cid = Column(Integer)
    references = Column(JSON, nullable=False)
    retrieved_at = Column(DateTime, nullable=False)
    confirmed_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    confirmed_at = Column(DateTime, nullable=False)
