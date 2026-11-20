from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, UUID4


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
    parent_taxon_key: Optional[str] = None
    common_name: Optional[str] = None
    authority: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class TaxonomySchemaIn(BaseModel):
    taxon_name: str
    gbif_key: str
    parent_taxon_key: Optional[str] = None
    common_name: Optional[str] = None
    authority: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
