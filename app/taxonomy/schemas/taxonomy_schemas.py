from enum import Enum
from typing import Optional

from pydantic import BaseModel, UUID4


class TaxonRank(Enum):
    FORM = "form"
    VARIETY = "variety"
    SUBSPECIES = "subspecies"
    SPECIES = "species"
    GENUS = "genus"
    FAMILY = "family"
    ORDER = "order"
    CLASS = "class"
    PHYLUM = "phylum"
    KINGDOM = "kingdom"


TAXON_DICT = {
    "FORM": TaxonRank.FORM,
    "VARIETY": TaxonRank.VARIETY,
    "SUBSPECIES": TaxonRank.SUBSPECIES,
    "SPECIES": TaxonRank.SPECIES,
    "GENUS": TaxonRank.GENUS,
    "FAMILY": TaxonRank.FAMILY,
    "ORDER": TaxonRank.ORDER,
    "CLASS": TaxonRank.CLASS,
    "PHYLUM": TaxonRank.PHYLUM,
    "KINGDOM": TaxonRank.KINGDOM
}


class TaxonomySchema(BaseModel):
    taxon_id: UUID4
    taxon_name: str
    gbif_key: str
    taxon_rank: TaxonRank
    parent_taxon_key: Optional[str]
    common_name: Optional[str]
    authority: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class TaxonomySchemaIn(BaseModel):
    taxon_name: str
    gbif_key: str
    parent_taxon_key: Optional[str]
    common_name: Optional[str]
    authority: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
