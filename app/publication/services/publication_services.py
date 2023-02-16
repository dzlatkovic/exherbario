"""
This module defines a PublicationService class, which provides an
interface to the PublicationRepository for creating,
reading, and deleting Publication objects.
"""


from app.publication.models import Publication
from app.db import SessionLocal
from app.publication.repository import PublicationRepository
from app.publication.exceptions import PublicationExceptionDoi


class PublicationService:
    """
    Provides an interface to the PublicationRepository for creating,
    reading, and deleting Publication objects.
    """
    @staticmethod
    def create_new_publication(doi: str, year: str, journal: str,
                               title: str) -> PublicationExceptionDoi or Publication:
        """
        Creates a new Publication object with the specified DOI, year, journal, and title
        :param doi: The DOI of the publication
        :param year: The publication year
        :param journal: The journal in which the publication was published
        :param title: The title of the publication
        :return: The newly created Publication object
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                publication = repository.read_publication_by_doi(doi)
                if publication is None:
                    return repository.create_publication(doi, year, journal, title)
                raise PublicationExceptionDoi(message="Publication exists in the database.",
                                              code=400)
        except Exception as error:
            raise error

    @staticmethod
    def read_all():
        """
        Reads all Publication objects from the database
        :return: A list of Publication objects
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_all()
        except Exception as error:
            raise error

    @staticmethod
    def read_publication_by_id(pub_id: str):
        """
        Reads a Publication object with the specified ID from the database
        :param pub_id: The ID of the Publication to read
        :return: The Publication object with the specified ID
        :raises Exception: If an error occurs while reading the Publication object
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_publication_by_id(pub_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_publication_by_id(pub_id: str):
        """
        Deletes a Publication object with the specified ID from the database
        :param pub_id: The ID of the Publication to delete
        :return: True if the Publication was successfully deleted
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.delete_publication(pub_id)
        except Exception as error:
            raise error
