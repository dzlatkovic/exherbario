"""
This module contains the PublicationController class,
which provides API endpoints for managing publications.
"""

from fastapi import HTTPException, Response

from app.publication.schemas import PublicationSchemaUpdate
from app.publication.services import PublicationService
from app.publication.exceptions import PublicationExceptionDoi, PublicationNotFoundException


class PublicationController:
    """
    Controller class for Publication-related API endpoints.
    """
    @staticmethod
    def create_new_publication(doi: str, year: str, journal: str, title: str, abstract: str):
        """
        Creates a new publication with the provided information
        :param doi: Digital Object Identifier of the publication
        :param year: Publication year
        :param journal: Journal in which the publication was published
        :param title: Title of the publication
        :param abstract: Publication abstract
        :return: JSON representation of the created publication
        """
        try:
            return PublicationService.create_new_publication(doi, year, journal, title, abstract)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PublicationExceptionDoi as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_all():
        """
        Retrieves all publications
        :return: List of JSON representations of publications.
        """
        return PublicationService.read_all()

    @staticmethod
    def get_publication_by_id(pub_id: str):
        """
        Retrieves a publication by ID
        :param pub_id: ID of the publication to retrieve
        :return: JSON representation of the retrieved publication
        """
        try:
            return PublicationService.read_publication_by_id(pub_id)
        except PublicationNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_publication_by_id(pub_id: str):
        """
        Deletes a publication by ID
        :param pub_id: ID of the publication to delete
        :return: HTTP response indicating success or failure
        """
        try:
            PublicationService.delete_publication_by_id(pub_id)
            return Response(content=f"Publication with the provided ID: "
                                    f"{pub_id} deleted.", status_code=200)
        except PublicationNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def update_publication(pub_id: str, publication: PublicationSchemaUpdate):
        """
        It updates a publication.

        :param pub_id: str - The id of the publication to update
        :type pub_id: str
        :param publication: PublicationSchemaUpdate
        :type publication: PublicationSchemaUpdate
        :return: The updated publication
        """
        try:
            return PublicationService.update_publication(pub_id, publication)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except PublicationNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
