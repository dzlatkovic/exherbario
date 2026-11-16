from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, ForeignKey, JSON, String

from app.db import Base, new_id


def utc_now():
    return datetime.now(timezone.utc).replace(tzinfo=None)


class PCAAnalysis(Base):
    __tablename__ = "chemistry_pca"

    id = Column(String(50), primary_key=True, default=new_id)
    study_id = Column(String(50), ForeignKey("chemistry_study.id"), nullable=False)
    created_by = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    created_at = Column(DateTime, nullable=False, default=utc_now)
    profile_ids = Column(JSON, nullable=False)
    configuration = Column(JSON, nullable=False)
    results = Column(JSON, nullable=False)
