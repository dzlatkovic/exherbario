"""Cached provider answers and the record of what a curator accepted from them."""

from sqlalchemy import JSON, Boolean, Column, DateTime, ForeignKey, Index, String, Text

from app.db import Base, new_id


class ExternalLookupCache(Base):
    """One provider answer, reused until it expires and served (marked stale) while the provider is down."""
    __tablename__ = "external_lookup_cache"

    provider = Column(String(40), primary_key=True)
    key_digest = Column(String(64), primary_key=True)  # SHA-256 of the normalized request
    lookup_key = Column(Text, nullable=False)
    found = Column(Boolean, nullable=False)
    payload = Column(JSON)
    fetched_at = Column(DateTime, nullable=False)


class ExternalImport(Base):
    """Written only when a curator saves a record with values taken from a provider."""
    __tablename__ = "external_import"
    __table_args__ = (Index("ix_external_import_record", "record_type", "record_id"),)

    id = Column(String(50), primary_key=True, default=new_id)
    provider = Column(String(40), nullable=False)
    external_id = Column(String(300), nullable=False)
    record_type = Column(String(20), nullable=False)  # taxon, publication or institution
    record_id = Column(String(50), nullable=False)
    fields = Column(JSON, nullable=False)
    retrieved_at = Column(DateTime)
    confirmed_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    confirmed_at = Column(DateTime, nullable=False)
