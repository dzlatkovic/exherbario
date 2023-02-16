"""
This module defines the Pydantic schemas for the Photos model.
"""


from pydantic import BaseModel, UUID4


class PhotosSchema(BaseModel):
    """
    Pydantic schema representing a photos object returned by the API.

    Attributes:
        photos_id (UUID4): The UUID for the photos object.
        field_photo (str): The file path for the field photo.
        specimen_photo (str): The file path for the specimen photo.
    """
    photos_id: UUID4
    field_photo: str
    specimen_photo: str

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class PhotosSchemaIn(BaseModel):
    """
    Pydantic schema representing the input for creating a new photos object via the API.

    Attributes:
        field_photo (str): The file path for the field photo.
        specimen_photo (str): The file path for the specimen photo.
    """
    field_photo: str
    specimen_photo: str

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
