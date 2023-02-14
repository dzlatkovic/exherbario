from uuid import uuid4

from sqlalchemy import Column, ForeignKey, String, UniqueConstraint

from app.db import Base


class SpecimenPublication(Base):
    __tablename__ = "specimen_publication"
    specimen_publication_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    publication_id = Column(String(50), ForeignKey("publication.pub_id"))
    __table_args__ = (UniqueConstraint("specimen_id", "publication_id",
                                       name="publication_authors_uc"),)

    def __init__(self, specimen_id: str, publication_id: str):
        self.specimen_id = specimen_id
        self.publication_id = publication_id
