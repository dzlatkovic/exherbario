from sqlalchemy import select

from .models import Deposition


def draft_reference(db, field: str, record_ids: set[str], actor=None) -> str | None:
    """Identify a draft without revealing another researcher's private title."""
    if not record_ids:
        return None
    drafts = db.execute(select(Deposition.draft, Deposition.owner_id).where(Deposition.draft.is_not(None)))
    for draft, owner in drafts:
        if record_ids.intersection(draft.get(field, [])):
            title = draft.get("title")
            if title and (actor is None or actor.is_superuser or actor.user_id == owner):
                return f'the deposition draft “{title}”'
            return "a deposition draft"
    return None
