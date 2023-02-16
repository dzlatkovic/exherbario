"""
This module defines the `Storage` class, which represents a storage box.
"""
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
    room = Column(String(20))
    shelf = Column(String(20))
    box = Column(String(100), unique=True)

    def __init__(self, room: str, shelf: str, box: str):
        """
        Initializes a new instance of the Storage class
        :param room: The name or number of the room
        :type room: str
        :param shelf: The name or number of the shelf
        :type shelf: str
        :param box: The unique identifier of the box
        :type box: str
        """
        self.room = room
        self.shelf = shelf
        self.box = box
