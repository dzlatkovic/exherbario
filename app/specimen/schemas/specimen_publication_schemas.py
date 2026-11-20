"""This module contains Pydantic models for SpecimenPublication objects."""


from pydantic import BaseModel, ConfigDict
from pydantic.types import UUID4


class SpecimenPublicationSchema(BaseModel):
    """
    A Pydantic model that represents a SpecimenPublication object.
    """
    specimen_publication_id: UUID4
    specimen_id: str
    publication_id: str

    model_config = ConfigDict(from_attributes=True)


class SpecimenPublicationSchemaIn(BaseModel):
    """
    A Pydantic model that represents the input data for creating a
    SpecimenPublication object.
    """
    specimen_id: str
    publication_id: str

    model_config = ConfigDict(from_attributes=True)
