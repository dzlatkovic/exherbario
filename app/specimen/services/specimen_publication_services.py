from app.db import SessionLocal
from app.specimen.repository import SpecimenPublicationRepository


class SpecimenPublicationService:

    @staticmethod
    def create_new_specimen_publication(specimen_id: str, publication_id: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenPublicationRepository(db)
                return repository.create_specimen_publication(specimen_id, publication_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_specimen_publication_by_id(specimen_publication_id: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenPublicationRepository(db)
                return repository.delete_specimen_publication_by_id(specimen_publication_id)
        except Exception as e:
            raise e
