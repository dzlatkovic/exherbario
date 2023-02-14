from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base


class PublicationAuthors(Base):
    __tablename__ = "publication_authors"
    publication_authors_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    user_id = Column(String(50), ForeignKey("users.user_id"))
    publication_id = Column(String(50), ForeignKey("publication.pub_id"))
    __table_args__ = (UniqueConstraint("user_id", "publication_id",
                                       name="publication_authors_uc"),)

    def __init__(self, user_id: str, publication_id: str):
        self.user_id = user_id
        self.publication_id = publication_id
