"""
This module defines Pydantic schemas for the
PublicationAuthors model.
"""


from pydantic import BaseModel, ConfigDict
from pydantic.types import UUID4


class PublicationAuthorsSchema(BaseModel):
    """
    Pydantic schema for the PublicationAuthors model.
    """
    publication_authors_id: UUID4
    user_id: str
    publication_id: str

    model_config = ConfigDict(from_attributes=True)


class PublicationAuthorsSchemaIn(BaseModel):
    """
    Pydantic input schema for the PublicationAuthors model.
    """
    user_id: str
    publication_id: str

    model_config = ConfigDict(from_attributes=True)
