"""
This module defines the Pydantic schema classes for the field location endpoint.

The `FieldLocSchema` class defines the schema for a field location object
that is returned by the API.
The `FieldLocSchemaIn` class defines the schema for a field location object
that is used as input for creating a new
field location object.
These classes are used to validate input data and serialize/deserialize JSON data.
"""
from typing import Optional

from pydantic import BaseModel, Field, UUID4, constr


class FieldLocSchema(BaseModel):
    """
    Schema class for a field location object.

    This class defines the schema for a field location object. It includes the attributes
    of a field location, along with a configuration that allows it to be used with the
    SQLAlchemy ORM.
    """
    field_loc_id: UUID4
    country: str
    region: str
    locality: str
    altitude: Optional[int] = None
    habitat: Optional[str] = None
    gps_lat: Optional[float] = None
    gps_long: Optional[float] = None
    coordinate_uncertainty_m: Optional[int] = None
    geodetic_datum: Optional[str] = None
    georeference_source: Optional[str] = None

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class FieldLocSchemaIn(BaseModel):
    """
    Schema class for a field location input.

    This class defines the schema for a field location input. It includes the attributes
    of a field location, along with a configuration that allows it to be used with the
    SQLAlchemy ORM.
    """
    country: constr(max_length=100)
    region: constr(max_length=150)
    locality: constr(max_length=500)
    altitude: Optional[int] = None
    habitat: Optional[constr(max_length=255)] = None
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_long: Optional[float] = Field(None, ge=-180, le=180)
    coordinate_uncertainty_m: Optional[int] = Field(None, ge=0, le=20_037_509)
    geodetic_datum: Optional[constr(strip_whitespace=True, max_length=20)] = None
    georeference_source: Optional[constr(strip_whitespace=True, max_length=200)] = None

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class FieldLocSchemaUpdate(BaseModel):
    """
    Schema class for a field location update input.
    """
    country: Optional[constr(max_length=100)]
    region: Optional[constr(max_length=150)]
    locality: Optional[constr(max_length=500)]
    altitude: Optional[int]
    habitat: Optional[constr(max_length=255)]
    gps_lat: Optional[float] = Field(None, ge=-90, le=90)
    gps_long: Optional[float] = Field(None, ge=-180, le=180)
    coordinate_uncertainty_m: Optional[int] = Field(None, ge=0, le=20_037_509)
    geodetic_datum: Optional[constr(strip_whitespace=True, max_length=20)]
    georeference_source: Optional[constr(strip_whitespace=True, max_length=200)]
    correction_reason: Optional[constr(strip_whitespace=True, min_length=1, max_length=1000)] = None

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
