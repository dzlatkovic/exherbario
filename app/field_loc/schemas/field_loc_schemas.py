"""
This module defines the Pydantic schema classes for the field location endpoint.

The `FieldLocSchema` class defines the schema for a field location object
that is returned by the API.
The `FieldLocSchemaIn` class defines the schema for a field location object
that is used as input for creating a new
field location object.
These classes are used to validate input data and serialize/deserialize JSON data.
"""


from pydantic import BaseModel, UUID4, validator


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

    @classmethod
    @validator('gps_lat')
    def gps_lat_must_be_float(cls, value):
        """
        Validates that the gps_lat is a float
        :param cls: The class
        :param value: The gps_lat value to be validated
        :return: The gps_lat value if it is valid
        :raises ValueError: If the gps_lat is not a float
        """
        if not isinstance(value, float):
            raise ValueError('gps_lat must be a float')
        return value

    @classmethod
    @validator('gps_long')
    def gps_long_must_be_float(cls, value):
        """
        Validates that the gps_long is a float
        :param cls: The class
        :param value: The gps_long value to be validated
        :return: The gps_long value if it is valid
        :raises ValueError: If the gps_long is not a float
        """
        if not isinstance(value, float):
            raise ValueError('gps_long must be a float')
        return value

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
