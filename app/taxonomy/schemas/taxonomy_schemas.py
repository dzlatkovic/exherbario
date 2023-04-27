from enum import Enum
from typing import Optional

from pydantic import BaseModel, UUID4


class TaxonRank(Enum):
    form = "form"
    variety = "variety"
    subspecies = "subspecies"
    species = "species"
    genus = "genus"
    family = "family"
    order = "order"
    CLASS = "class"
    phylum = "phylum"
    kingdom = "kingdom"


class TaxonomySchema(BaseModel):
    taxon_id: UUID4
    taxon_name: str
    gbif_key: str
    taxon_rank: TaxonRank
    parent_gbif_key: Optional[str]
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
    parent_gbif_key: Optional[str]
    common_name: Optional[str]
    authority: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
