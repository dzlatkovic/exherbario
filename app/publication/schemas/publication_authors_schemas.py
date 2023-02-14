from pydantic import BaseModel
from pydantic.types import UUID4


class PublicationAuthorsSchema(BaseModel):
    publication_authors_id: UUID4
    user_id: str
    publication_id: str

    class Config:
        orm_mode = True


class PublicationAuthorsSchemaIn(BaseModel):
    user_id: str
    publication_id: str

    class Config:
        orm_mode = True
