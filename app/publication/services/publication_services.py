from app.publication.models import Publication
from app.db import SessionLocal
from app.publication.repository import PublicationRepository
from app.publication.exceptions import PublicationExceptionDoi


class PublicationService:

    @staticmethod
    def create_new_publication(doi: str, year: str, journal: str,
                               title: str) -> PublicationExceptionDoi or Publication:
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                publication = repository.read_publication_by_doi(doi)
                if publication is None:
                    return repository.create_publication(doi, year, journal, title)
                raise PublicationExceptionDoi(message="Publication already exists in the database.", code=400)
        except Exception as e:
            raise e

    @staticmethod
    def read_all():
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_all()
        except Exception as e:
            raise e

    @staticmethod
    def read_publication_by_id(pub_id: str):
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_publication_by_id(pub_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_publication_by_id(pub_id: str):
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.delete_publication(pub_id)
        except Exception as e:
            raise e
