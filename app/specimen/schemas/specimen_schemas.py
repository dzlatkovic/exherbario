"""This module contains Pydantic models for working with specimen data."""


from datetime import date
from typing import Optional

from pydantic import BaseModel, UUID4, constr


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
    correction_reason: Optional[constr(strip_whitespace=True, min_length=1, max_length=1000)] = None
