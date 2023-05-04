from datetime import datetime

from pydantic import BaseModel, UUID4


class RevisionSchema(BaseModel):
    revision_id: UUID4
    timestamp: datetime
    revised_by: str
    specimen_id: str
    prev_taxon_id: str
    prev_subnomen: str

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class RevisionSchemaIn(BaseModel):
    revised_by: str
    specimen_id: str
    prev_taxon_id: str
    prev_subnomen: str

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
