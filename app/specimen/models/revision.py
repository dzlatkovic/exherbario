from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey

from app.db import Base, new_id


class Revision(Base):
    __tablename__ = "revision"
    revision_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    timestamp = Column(DateTime)
    revised_by = Column(String(50), ForeignKey("users.user_id"))
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    prev_taxon_id = Column(String(50), ForeignKey("taxonomy.taxon_id"))
    prev_subnomen = Column(String(200))

    def __init__(self,
                 revised_by: str,
                 specimen_id: str,
                 prev_taxon_id: str,
                 prev_subnomen: str):
        self.revised_by = revised_by
        self.specimen_id = specimen_id
        self.prev_taxon_id = prev_taxon_id
        self.prev_subnomen = prev_subnomen
        self.timestamp = datetime.utcnow()
