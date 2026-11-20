from datetime import date, datetime

from typing import Optional

from pydantic import BaseModel, Field, UUID4
from .specimen_schemas import PersonName


class RevisionSchema(BaseModel):
    revision_id: UUID4
    timestamp: datetime
    revised_by: str
    specimen_id: str
    prev_taxon_id: Optional[str]
    prev_subnomen: Optional[str]
    prev_determiner_name: Optional[str]
    prev_determination_date: Optional[date]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class RevisionSchemaIn(BaseModel):
    specimen_id: str
    taxon_id: str = Field(min_length=1)
    subnomen: Optional[str] = Field(default=None, min_length=1)
    determiner_name: PersonName | None = None
    determination_date: date | None = None

    class Config:
        extra = "forbid"
