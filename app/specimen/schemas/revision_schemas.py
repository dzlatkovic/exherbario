from datetime import datetime

from typing import Optional

from pydantic import BaseModel, Field, UUID4


class RevisionSchema(BaseModel):
    revision_id: UUID4
    timestamp: datetime
    revised_by: str
    specimen_id: str
    prev_taxon_id: Optional[str]
    prev_subnomen: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class RevisionSchemaIn(BaseModel):
    specimen_id: str
    taxon_id: str = Field(min_length=1)
    subnomen: Optional[str] = Field(default=None, min_length=1)

    class Config:
        extra = "forbid"
