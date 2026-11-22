from sqlalchemy import false, Boolean, Column, ForeignKey, String, Text

from app.db import Base, new_id


class Study(Base):
    __tablename__ = "chemistry_study"

    id = Column(String(50), primary_key=True, default=new_id)
    owner_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    publication_id = Column(String(50), ForeignKey("publication.pub_id"))
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=False)
    is_public = Column(Boolean, nullable=False, default=False)
    ever_public = Column(Boolean, nullable=False, server_default=false())
