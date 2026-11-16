"""
This module defines the PublicationAuthors class, which represents
a mapping between publications and authors in the database.
"""


from sqlalchemy import Column, ForeignKey, String, UniqueConstraint
from app.db import Base, new_id


class PublicationAuthors(Base):
    """
    Represents a mapping between publications and authors in the database.

    Attributes:
        publication_authors_id (str): Unique identifier for the publication author mapping.
        user_id (str): Unique identifier for the user associated with the publication.
        publication_id (str): Unique identifier for the publication associated with the user.
    """
    __tablename__ = "publication_authors"
    publication_authors_id = Column(String(50), primary_key=True, default=new_id,
                                    autoincrement=False)
    user_id = Column(String(50), ForeignKey("users.user_id"))
    publication_id = Column(String(50), ForeignKey("publication.pub_id"))
    __table_args__ = (UniqueConstraint("user_id", "publication_id",
                                       name="publication_authors_uc"),)

    def __init__(self, user_id: str, publication_id: str):
        """
        Initializes a new PublicationAuthors object
        :param user_id: Unique identifier for the user associated with the publication
        :param publication_id: Unique identifier for the publication associated with the user
        """
        self.user_id = user_id
        self.publication_id = publication_id
