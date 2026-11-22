"""Saved run conditions and preparation methods. They only prefill forms: results keep their own copy."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import ConditionPreset
from app.chemistry.sample_links import utc_now
from app.chemistry.schemas.chemistry_schemas import ConditionPresetIn
from app.users.models import User

MAX_PRESETS = 200


def preset_summary(preset: ConditionPreset) -> dict:
    return {"id": preset.id, "kind": preset.kind, "name": preset.name, "values": preset.values,
            "updated_at": preset.updated_at}


class PresetService:
    def __init__(self, db: Session):
        self.db = db

    def list(self, actor: User, kind: str | None = None):
        query = select(ConditionPreset).where(ConditionPreset.owner_id == actor.user_id)
        if kind is not None:
            query = query.where(ConditionPreset.kind == kind)
        return self.db.scalars(query.order_by(ConditionPreset.kind, ConditionPreset.name)).all()

    def save(self, data: ConditionPresetIn, actor: User) -> ConditionPreset:
        """Save under a name; saving again under the same name replaces the values."""
        preset = self.db.scalar(select(ConditionPreset).where(
            ConditionPreset.owner_id == actor.user_id, ConditionPreset.kind == data.kind,
            ConditionPreset.name == data.name))
        if preset is None:
            if len(self.list(actor, data.kind)) >= MAX_PRESETS:
                raise ChemistryError(409, f"You can save at most {MAX_PRESETS} of these. Delete one you no longer use.")
            preset = ConditionPreset(owner_id=actor.user_id, kind=data.kind, name=data.name)
            self.db.add(preset)
        preset.values, preset.updated_at = data.values, utc_now()
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ChemistryError(409, "A saved entry with this name was just created. Try again.") from error
        return preset

    def delete(self, preset_id: str, actor: User):
        preset = self.db.get(ConditionPreset, preset_id)
        if preset is None or preset.owner_id != actor.user_id:
            raise ChemistryError(404, "Saved conditions not found.")
        self.db.delete(preset)
        self.db.commit()
