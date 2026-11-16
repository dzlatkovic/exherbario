"""
This module defines the Publication class, which represents a
publication in the database.
"""


from datetime import datetime
from sqlalchemy import Column, String, Date, Text

from app.db import Base, new_id


class Publication(Base):
    """
    Represents a publication in the database.
    Attributes:
        pub_id (str): Unique identifier for the publication.
        doi (str): Digital Object Identifier for the publication.
        year (datetime): Date representing the year in which the publication was published.
        journal (str): Name of the journal in which the publication was published.
        title (str): Title of the publication.
    """
    __tablename__ = "publication"
    pub_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    doi = Column(String(200), nullable=False)
    year = Column(Date)
    journal = Column(String(100))
    title = Column(String(200))
    abstract = Column(Text)

    def __init__(self, doi: str, year: str, journal: str, title: str, abstract: str):
        """
        Initializes a new Publication object
        :param doi: Digital Object Identifier for the publication
        :param year: The year in which the publication was published (format: YYYY)
        :param journal: Name of the journal in which the publication was published
        :param title: Title of the publication.
        """
        self.doi = doi
        self.year = datetime.strptime(year, "%Y")
        self.journal = journal
        self.title = title
        self.abstract = abstract
