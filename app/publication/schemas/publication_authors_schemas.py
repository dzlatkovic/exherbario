"""
This module defines Pydantic schemas for the
PublicationAuthors model.
"""


from pydantic import BaseModel
from pydantic.types import UUID4


class PublicationAuthorsSchema(BaseModel):
    """
    Pydantic schema for the PublicationAuthors model.
    """
    publication_authors_id: UUID4
    user_id: str
    publication_id: str

    class Config:
        """
        Pydantic model configuration options for
        the PublicationAuthors schema.
        """
        orm_mode = True


class PublicationAuthorsSchemaIn(BaseModel):
    """
    Pydantic input schema for the PublicationAuthors model.
    """
    user_id: str
    publication_id: str

    class Config:
        """
        Pydantic model configuration options for
        the PublicationAuthors schema.
        """
        orm_mode = True
