"""
This module defines a PublicationAuthorsService class,
which provides an interface to the PublicationAuthorsRepository for
creating and deleting PublicationAuthors objects.
"""


from app.db import SessionLocal
from app.publication.repository import PublicationAuthorsRepository


class PublicationAuthorsService:
    """
    Provides an interface to the PublicationAuthorsRepository
    for creating and deleting PublicationAuthors objects.
    """
    @staticmethod
    def create_new_publication_authors(user_id: str, publication_id: str):
        """
        Creates a new PublicationAuthors object with the specified user ID and publication ID
        :param user_id: The ID of the user who authored the publication
        :param publication_id: The ID of the publication
        :return: The newly created PublicationAuthors object
        """
        try:
            with SessionLocal() as db:
                repository = PublicationAuthorsRepository(db)
                return repository.create_publication_authors(user_id, publication_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_publication_authors_by_id(publication_authors_id: str):
        """
        Deletes a PublicationAuthors object with the specified ID from the database
        :param publication_authors_id: The ID of the PublicationAuthors object to delete
        :return: True if the PublicationAuthors object was successfully deleted
        """
        try:
            with SessionLocal() as db:
                repository = PublicationAuthorsRepository(db)
                return repository.delete_publication_authors_by_id(publication_authors_id)
        except Exception as error:
            raise error

    @staticmethod
    def get_publication_report():
        """
        It returns a dictionary of dictionaries, where the keys are
        the DOIs of the publications, and the values are
        dictionaries with the keys "authors" and "species",
        which contain lists of authors and species, respectively
        :return: A dictionary with the DOI as the key and a
        dictionary as the value. The value dictionary has two keys:
        authors and species. The authors key has a list of
        authors as the value. The species key has a list of species as
        the value.
        """
        try:
            with SessionLocal() as db:
                repository = PublicationAuthorsRepository(db)
                return repository.get_publication_report()
        except Exception as error:
            raise error
