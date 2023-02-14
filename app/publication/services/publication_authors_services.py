from app.db import SessionLocal
from app.publication.repository import PublicationAuthorsRepository


class PublicationAuthorsService:

    @staticmethod
    def create_new_publication_authors(user_id: str, publication_id: str):
        try:
            with SessionLocal() as db:
                repository = PublicationAuthorsRepository(db)
                return repository.create_publication_authors(user_id, publication_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_publication_authors_by_id(publication_authors_id: str):
        try:
            with SessionLocal() as db:
                repository = PublicationAuthorsRepository(db)
                return repository.delete_publication_authors_by_id(publication_authors_id)
        except Exception as e:
            raise e
