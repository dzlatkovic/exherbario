"""
This module defines the PublicationRepository class,
which provides methods for managing publications in the database.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.publication.models import Publication
from app.publication.exceptions import PublicationNotFoundException


class PublicationRepository:
    """
    Repository class for managing publications in the database.
    """
    def __init__(self, db: Session):
        """
        Initializes a new PublicationRepository object
        :param db: Database session object
        """
        self.db = db

    def create_publication(self, doi: str, year: str, journal: str, title: str):
        """
        Creates a new publication with the provided information
        :param doi: Digital Object Identifier for the publication
        :param year:The year in which the publication was published (format: YYYY)
        :param journal: Name of the journal in which the publication was published
        :param title: Title of the publication
        :return: Publication object representing the created publication.
        """
        try:
            publication = Publication(doi, year, journal, title)
            self.db.add(publication)
            self.db.commit()
            self.db.refresh(publication)
            return publication
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

    def read_all(self):
        """
        Reads all publications in the database
        :return: List of Publication objects
        """
        return self.db.query(Publication).all()

    def read_publication_by_id(self, pub_id: str):
        """
        Reads a publication by ID
        :param pub_id: ID of the publication to retrieve
        :return: Publication object representing the retrieved publication
        """
        publication = self.db.query(Publication).filter(Publication.pub_id == pub_id).first()
        if publication is None:
            raise PublicationNotFoundException(f"Publication with the provided ID: "
                                               f"{pub_id} not found.", 400)
        return publication

    def delete_publication(self, pub_id: str):
        """
        Deletes a publication by ID
        :param pub_id: ID of the publication to delete
        :return: True if the publication was successfully deleted
        """
        try:
            publication = self.db.query(Publication).filter(Publication.pub_id == pub_id).first()
            if publication is None:
                raise PublicationNotFoundException(f"Publication with provided ID: "
                                                   f"{pub_id} not found.", 400)
            self.db.delete(publication)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def read_publication_by_doi(self, doi: str):
        """
        Reads a publication by DOI
        :param doi: Digital Object Identifier for the publication
        :return: Publication object representing the retrieved publication
        """
        return self.db.query(Publication).filter(Publication.doi == doi).first()
