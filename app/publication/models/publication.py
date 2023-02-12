from datetime import datetime
from sqlalchemy import Column, String, Date
from uuid import uuid4

from app.db import Base


class Publication(Base):
    __tablename__ = "publication"
    pub_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    doi = Column(String(200))
    year = Column(Date)
    journal = Column(String(100))
    title = Column(String(200))

    def __init__(self, doi: str, year: str, journal: str, title: str):
        self.doi = doi
        self.year = datetime.strptime(year, "%Y")
        self.journal = journal
        self.title = title
