"""This module contains the Pydantic schemas for the storage module."""
from typing import Optional

from pydantic import BaseModel, UUID4


class StorageSchema(BaseModel):
    """
    Pydantic schema for the Storage model
    :param storage_id: The ID of the storage
    :type storage_id: UUID4
    :param room: The room of the storage
    :type room: str
    :param shelf: The shelf of the storage
    :type shelf: str
    :param box: The box of the storage
    :type box: str
    """
    storage_id: UUID4
    box: str
    room: Optional[str]
    shelf: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class StorageSchemaIn(BaseModel):
    """
    Pydantic schema for the input to create a new storage
    :param room: The room of the storage
    :type room: str
    :param shelf: The shelf of the storage
    :type shelf: str
    :param box: The box of the storage
    :type box: str
    """
    box: str
    room: Optional[str]
    shelf: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class StorageSchemaUpdate(BaseModel):
    """
    Pydantic schema for updating an existing storage
    :param room: The new room of the storage
    :type room: str
    :param shelf: The new shelf of the storage
    :type shelf: str
    """
    room: Optional[str]
    shelf: Optional[str]

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
