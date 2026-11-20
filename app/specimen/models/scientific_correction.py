"""Preserve the provenance of changes to vouchers and their collection sites."""

from datetime import datetime, timezone

from fastapi.encoders import jsonable_encoder
from sqlalchemy import JSON, CheckConstraint, Column, DateTime, ForeignKey, String, Text

from app.db import Base, new_id


class ScientificCorrection(Base):
    __tablename__ = "scientific_correction"
    __table_args__ = (
        CheckConstraint(
            "(specimen_id IS NOT NULL AND field_loc_id IS NULL) OR "
            "(specimen_id IS NULL AND field_loc_id IS NOT NULL)",
            name="scientific_correction_one_target",
        ),
        {"mysql_engine": "InnoDB"},
    )

    id = Column(String(50), primary_key=True, default=new_id)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"), index=True)
    field_loc_id = Column(String(50), ForeignKey("field_loc.field_loc_id"), index=True)
    actor_id = Column(String(50), ForeignKey("users.user_id"), nullable=False)
    timestamp = Column(DateTime, nullable=False)
    reason = Column(Text, nullable=False)
    old_values = Column(JSON, nullable=False)
    new_values = Column(JSON, nullable=False)

    def __init__(self, *, actor_id, reason, old_values, new_values, **target):
        if not actor_id or not reason or not reason.strip():
            raise ValueError("A curator and a correction reason are required.")
        super().__init__(
            actor_id=actor_id, reason=reason.strip(),
            timestamp=datetime.now(timezone.utc).replace(tzinfo=None),
            old_values=jsonable_encoder(old_values), new_values=jsonable_encoder(new_values),
            **target,
        )
