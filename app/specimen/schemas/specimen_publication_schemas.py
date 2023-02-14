from pydantic import BaseModel
from pydantic.types import UUID4


class SpecimenPublicationSchema(BaseModel):
    specimen_publication_id: UUID4
    specimen_id: str
    publication_id: str

    class Config:
        orm_mode = True


class SpecimenPublicationSchemaIn(BaseModel):
    specimen_id: str
    publication_id: str

    class Config:
        orm_mode = True
