"""
This module defines Pydantic schemas for the
Publication model.
"""

from datetime import date, datetime
from typing import Literal, Optional

from pydantic import BaseModel, ConfigDict, UUID4, constr, field_validator


class ExternalSource(BaseModel):
    """Where a curator took the values from: sent with a save after a lookup, stored as provenance."""
    provider: Literal["crossref"]
    external_id: constr(strip_whitespace=True, min_length=1, max_length=300)
    retrieved_at: Optional[str] = None


class PublicationSchema(BaseModel):
    """
    Pydantic schema for the Publication model.
    """
    pub_id: UUID4
    doi: str
    year: date
    journal: str
    title: str
    abstract: str

    model_config = ConfigDict(from_attributes=True)


class PublicationSchemaIn(BaseModel):
    """
    Pydantic input schema for the Publication model.
    """
    doi: str
    year: str
    journal: str
    title: str
    abstract: str
    source: Optional[ExternalSource] = None

    @field_validator('year')
    @classmethod
    def valid_year(cls, year):
        """
        It takes a string as input, and if it's a valid year, it returns the year.
        If it's not a valid year, it raises a ValueError
        :param cls: The class that the method is being called on
        :param year: The input value for year
        :return: The year is being returned.
        """
        try:
            datetime.strptime(year, '%Y')
            return year
        except ValueError as error:
            raise ValueError('Year must be a string of the format YYYY') from error

    model_config = ConfigDict(from_attributes=True)


class PublicationSchemaUpdate(BaseModel):
    """Pydantic model for updating a publication record."""
    doi: Optional[str] = None
    year: Optional[str] = None
    journal: Optional[str] = None
    title: Optional[str] = None
    abstract: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)
