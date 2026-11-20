from datetime import datetime
from sqlalchemy import Column, Date, String, DateTime, ForeignKey

from app.db import Base, new_id


class Revision(Base):
    __tablename__ = "revision"
    revision_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    timestamp = Column(DateTime)
    revised_by = Column(String(50), ForeignKey("users.user_id"))
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"))
    prev_taxon_id = Column(String(50), ForeignKey("taxonomy.taxon_id"))
    prev_subnomen = Column(String(200))
    prev_determiner_name = Column(String(200))
    prev_determination_date = Column(Date)

    def __init__(self,
                 revised_by: str,
                 specimen_id: str,
                 prev_taxon_id: str,
                 prev_subnomen: str,
                 prev_determiner_name=None,
                 prev_determination_date=None):
        self.revised_by = revised_by
        self.specimen_id = specimen_id
        self.prev_taxon_id = prev_taxon_id
        self.prev_subnomen = prev_subnomen
        self.prev_determiner_name = prev_determiner_name
        self.prev_determination_date = prev_determination_date
        self.timestamp = datetime.utcnow()
