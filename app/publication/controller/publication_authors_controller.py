"""This module contains the PublicationAuthorsController class,
which provides API endpoints for managing publication authors."""

from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Response

from app.publication.exceptions import (PublicationAuthorsNotFoundException,
                                        EntryAlreadyExistsException)
from app.publication.services import PublicationAuthorsService


class PublicationAuthorsController:
    """
    Controller class for handling PublicationAuthors API requests.
    """
    @staticmethod
    def create_new_publication_authors(user_id: str, publication_id: str):
        """
        Create a new publication author entry in the database
        :param user_id: The ID of the user associated with the publication
        :type user_id: str
        :param publication_id: The ID of the publication associated with the user
        :type publication_id: str
        """
        try:
            return PublicationAuthorsService.create_new_publication_authors(user_id, publication_id)
        except EntryAlreadyExistsException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except IntegrityError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_publication_authors_by_id(publication_authors_id: str):
        """
        Delete the publication author entry with the provided ID
        :param publication_authors_id: The ID of the publication author entry to delete
        :type publication_authors_id: str
        :return: A response indicating that the publication author entry was deleted
        :rtype: Response
        """
        try:
            PublicationAuthorsService.delete_publication_authors_by_id(publication_authors_id)
            return Response(content=f"Entry with the provided ID: "
                                    f"{publication_authors_id} deleted.", status_code=200)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PublicationAuthorsNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

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
            return PublicationAuthorsService.get_publication_report()
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
