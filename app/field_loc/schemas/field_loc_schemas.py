"""
This module defines the Pydantic schema classes for the field location endpoint.

The `FieldLocSchema` class defines the schema for a field location object
that is returned by the API.
The `FieldLocSchemaIn` class defines the schema for a field location object
that is used as input for creating a new
field location object.
These classes are used to validate input data and serialize/deserialize JSON data.
"""


from pydantic import BaseModel, UUID4


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
    altitude: int
    habitat: str
    gps_lat: float
    gps_long: float

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
    country: str
    region: str
    locality: str
    altitude: int
    habitat: str
    gps_lat: float
    gps_long: float

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
