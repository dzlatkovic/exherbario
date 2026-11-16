from app.db import SessionLocal
from app.specimen.repository import SpecimenRepository
from app.specimen.schemas import RevisionSchemaIn


class RevisionService:
    @staticmethod
    def create_revision(revision_data: RevisionSchemaIn, revised_by: str):
        with SessionLocal() as db:
            changes = revision_data.dict(exclude={"specimen_id"}, exclude_none=True)
            return SpecimenRepository(db).revise_identification(revision_data.specimen_id, changes, revised_by)
