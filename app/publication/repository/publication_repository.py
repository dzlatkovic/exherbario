from app.publication.models import Publication
from app.publication.exceptions import PublicationNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class PublicationRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_publication(self, doi: str, year: str, journal: str, title: str):
        try:
            publication = Publication(doi, year, journal, title)
            self.db.add(publication)
            self.db.commit()
            self.db.refresh(publication)
            return publication
        except IntegrityError as e:
            raise e
        except Exception as e:
            raise e

    def read_all(self):
        return self.db.query(Publication).all()

    def read_publication_by_id(self, pub_id: str):
        publication = self.db.query(Publication).filter(Publication.pub_id == pub_id).first()
        if publication is None:
            raise PublicationNotFoundException(f"Publication with the provided ID: {pub_id} not found.", 400)
        return publication

    def delete_publication(self, pub_id: str):
        try:
            publication = self.db.query(Publication).filter(Publication.pub_id == pub_id).first()
            if publication is None:
                raise PublicationNotFoundException(f"Publication with provided ID: {pub_id} not found.", 400)
            self.db.delete(publication)
            self.db.commit()
            return True
        except Exception as e:
            raise e

    def read_publication_by_doi(self, doi: str):
        return self.db.query(Publication).filter(Publication.doi == doi).first()
