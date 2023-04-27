"""
This module defines the `Storage` class, which represents a storage box.
"""

from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String, Enum

from app.db import Base
from app.taxonomy.schemas.taxonomy_schemas import TaxonRank


class Taxonomy(Base):
    __tablename__ = "taxonomy"
    taxon_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    taxon_name = Column(String(100), nullable=False)
    gbif_key = Column(String(20), nullable=False, unique=True)
    taxon_rank = Column(Enum(TaxonRank), nullable=False)
    parent_gbif_key = Column(String(30), nullable=True)
    common_name = Column(String(50), nullable=True)
    authority = Column(String(30), nullable=True)

    def __init__(self,
                 taxon_name: str,
                 gbif_key: str,
                 taxon_rank: TaxonRank,
                 parent_gbif_key: Optional[str] = None,
                 common_name: Optional[str] = None,
                 authority: Optional[str] = None):
        self.taxon_name = taxon_name
        self.gbif_key = gbif_key
        self.taxon_rank = taxon_rank
        self.parent_gbif_key = parent_gbif_key
        self.common_name = common_name
        self.authority = authority
