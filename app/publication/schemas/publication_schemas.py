"""
This module defines Pydantic schemas for the
Publication model.
"""

from datetime import date, datetime
from pydantic import BaseModel, UUID4, validator


class PublicationSchema(BaseModel):
    """
    Pydantic schema for the Publication model.
    """
    pub_id: UUID4
    doi: str
    year: date
    journal: str
    title: str

    class Config:
        """
        Pydantic model configuration options for
        the PublicationAuthors schema.
        """
        orm_mode = True


class PublicationSchemaIn(BaseModel):
    """
    Pydantic input schema for the Publication model.
    """
    doi: str
    year: str
    journal: str
    title: str

    @classmethod
    @validator('year')
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

    class Config:
        """
        Pydantic model configuration options for
        the PublicationAuthors schema.
        """
        orm_mode = True
