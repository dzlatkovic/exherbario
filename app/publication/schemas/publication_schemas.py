from pydantic import BaseModel, UUID4
from datetime import date


class PublicationSchema(BaseModel):
    pub_id: UUID4
    doi: str
    year: date
    journal: str
    title: str

    class Config:
        orm_mode = True


class PublicationSchemaIn(BaseModel):
    doi: str
    year: str
    journal: str
    title: str

    class Config:
        orm_mode = True
