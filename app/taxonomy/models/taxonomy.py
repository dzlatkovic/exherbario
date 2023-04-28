"""
This module defines the `Storage` class, which represents a storage box.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Enum, ForeignKey

from app.db import Base
from app.taxonomy.schemas.taxonomy_schemas import TaxonRank


class Taxonomy(Base):
    __tablename__ = "taxonomy"
    taxon_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    taxon_name = Column(String(100), nullable=False)
    gbif_key = Column(String(20), nullable=False, unique=True)
    taxon_rank = Column(Enum(TaxonRank), nullable=False)
    parent_taxon_key = Column(String(50), ForeignKey('taxonomy.taxon_id'), nullable=True)
    common_name = Column(String(50), nullable=True)
    authority = Column(String(30), nullable=True)

    def __init__(self,
                 taxon_name: str,
                 gbif_key: str,
                 taxon_rank: TaxonRank,
                 parent_taxon_key: Optional[str] = None,
                 common_name: Optional[str] = None,
                 authority: Optional[str] = None):
        if parent_taxon_key is None and taxon_rank != TaxonRank.KINGDOM:
            raise ValueError("Parent taxon key must be provided for all taxa except kingdoms")
        elif parent_taxon_key is not None and taxon_rank == TaxonRank.KINGDOM:
            raise ValueError("Kingdoms must not have a parent taxon key")
        self.taxon_name = taxon_name
        self.gbif_key = gbif_key
        self.taxon_rank = taxon_rank
        self.parent_taxon_key = parent_taxon_key
        self.common_name = common_name
        self.authority = authority
