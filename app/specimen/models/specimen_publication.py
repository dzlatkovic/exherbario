"""This module contains the SpecimenPublication class."""


from uuid import uuid4
from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from app.db import Base


class SpecimenPublication(Base):
    """
    A class that represents the many-to-many relationship between specimens and publications.
    """
    __tablename__ = "specimen_publication"
    specimen_publication_id = Column(String(50), primary_key=True, default=uuid4,
                                     autoincrement=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    publication_id = Column(String(50), ForeignKey("publication.pub_id"))
    __table_args__ = (UniqueConstraint("specimen_id", "publication_id",
                                       name="publication_authors_uc"),)

    def __init__(self, specimen_id: str, publication_id: str):
        """
        Constructs a new instance of the SpecimenPublication class
         with the given specimen_id and publication_id
        :param specimen_id: The ID of the specimen
        :type specimen_id: str
        :param publication_id: The ID of the publication
        :type publication_id: str
        """
        self.specimen_id = specimen_id
        self.publication_id = publication_id
