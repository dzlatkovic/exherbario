from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.publication.exceptions.publication_authors_exceptions import PublicationAuthorsNotFoundException
from app.publication.models import PublicationAuthors


class PublicationAuthorsRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_publication_authors(self, user_id: str, publication_id: str):
        try:
            publication_authors = PublicationAuthors(user_id, publication_id)
            self.db.add(publication_authors)
            self.db.commit()
            self.db.refresh(publication_authors)
            return publication_authors
        except IntegrityError as e:
            raise e

    def delete_publication_authors_by_id(self, publication_authors_id: str):
        try:
            publication_authors = self.db.query(PublicationAuthors).filter(PublicationAuthors.publication_authors_id
                                                                           == publication_authors_id).first()
            if publication_authors is None:
                raise PublicationAuthorsNotFoundException(
                    code=400,
                    message=f"Entry with an ID {publication_authors_id} not found",
                )
            self.db.delete(publication_authors)
            self.db.commit()
            return True
        except Exception as e:
            raise e
