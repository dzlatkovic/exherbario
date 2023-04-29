"""This module contains Pydantic models for working with specimen data."""


from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, UUID4, validator


class SpecimenSchema(BaseModel):
    """Pydantic model for a complete specimen record"""
    specimen_id: UUID4
    reg_no: str
    collection_date: date
    reg_date: date
    taxon_id: str
    subnomen: str
    field_loc_id: str
    storage_id: str
    collected_by: str
    verified_by: str

    class Config:
        """
        The configuration settings for the Pydantic model.
        """
        orm_mode = True


class SpecimenSchemaIn(BaseModel):
    """Pydantic model for a specimen record with required fields."""
    reg_no: str
    collection_date: str
    reg_date: str
    taxon_id: str
    subnomen: str
    field_loc_id: str
    storage_id: str
    collected_by: str
    verified_by: str

    @classmethod
    @validator('collection_date')
    def validate_collection_date(cls, value):
        """
        It takes a string as input, and if it's in the format of yyyy-mm-dd,
        it returns the string. Otherwise, it raises a ValueError
        :param cls: The class that the validator is being applied to
        :param value: The value that is being validated
        :return: The value of the date.
        """
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError as error:
            raise ValueError('Invalid date format, should be yyyy-mm-dd') from error

    @classmethod
    @validator('reg_date')
    def validate_reg_date(cls, value):
        """
        It takes a string as input, and if it's in the format of yyyy-mm-dd,
        it returns the string. Otherwise, it raises a ValueError
        :param cls: The class that the validator is being applied to
        :param value: The value that is being validated
        :return: The value is being returned.
        """
        try:
            datetime.strptime(value, '%Y-%m-%d')
            return value
        except ValueError as error:
            raise ValueError('Invalid date format, should be yyyy-mm-dd') from error

    class Config:
        """
        The configuration settings for the Pydantic model.
        """
        orm_mode = True


class SpecimenSchemaUpdate(BaseModel):
    """Pydantic model for updating a specimen record."""
    reg_no: Optional[str]
    collection_date: Optional[date]
    taxon_id: Optional[str]
    subnomen: Optional[str]
    field_loc_id: Optional[str]
    storage_id: Optional[str]
    collected_by: Optional[str]
    verified_by: Optional[str]
