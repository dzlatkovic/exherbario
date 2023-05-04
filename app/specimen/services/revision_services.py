from app.db import SessionLocal
from app.specimen.repository import RevisionRepository
from app.specimen.schemas import RevisionSchemaIn


class RevisionService:
    @staticmethod
    def create_revision(revision_data: RevisionSchemaIn):
        try:
            with SessionLocal() as db:
                repository = RevisionRepository(db)
                return repository.create_revision(revision_data)
        except Exception as error:
            raise error
