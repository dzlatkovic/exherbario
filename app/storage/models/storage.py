"""
This module defines the `Storage` class, which represents a storage box.
"""
from typing import Optional
from uuid import uuid4

from sqlalchemy import Column, String

from app.db import Base


class Storage(Base):
    """
    Represents a storage box in a room with a specific shelf and box number
    :param room: The name or number of the room
    :type room: str
    :param shelf: The name or number of the shelf
    :type shelf: str
    :param box: The unique identifier of the box
    :type box: str
    """
    __tablename__ = "storage"
    storage_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    box = Column(String(100), nullable=False, unique=True)
    room = Column(String(20), nullable=True)
    shelf = Column(String(20), nullable=True)

    def __init__(self, box: str, room: Optional[str] = None, shelf: Optional[str] = None):
        """
        Initializes a new instance of the Storage class
        :param room: The name or number of the room
        :type room: str
        :param shelf: The name or number of the shelf
        :type shelf: str
        :param box: The unique identifier of the box
        :type box: str
        """
        self.box = box
        self.room = room
        self.shelf = shelf
