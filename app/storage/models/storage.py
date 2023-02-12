from sqlalchemy import Column, String
from uuid import uuid4

from app.db import Base


class Storage(Base):
    __tablename__ = "storage"
    storage_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    room = Column(String(20))
    shelf = Column(String(20))
    box = Column(String(100), unique=True)

    def __init__(self, room: str, shelf: str, box: str):
        self.room = room
        self.shelf = shelf
        self.box = box
