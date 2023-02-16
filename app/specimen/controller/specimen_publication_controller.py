"""
specimen_publication controller layer
"""


from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Response

from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.services import SpecimenPublicationService


class SpecimenPublicationController:
    """This class is responsible for the publication of specimen data"""
    @staticmethod
    def create_new_specimen_publication(specimen_id: str, publication_id: str):
        """
        It creates a new specimen_publication entry in the database
        :param specimen_id: str
        :type specimen_id: str
        :param publication_id: str
        :type publication_id: str
        :return: a new specimen publication entry.
        """
        try:
            return SpecimenPublicationService.create_new_specimen_publication(
                specimen_id, publication_id)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except IntegrityError as exc:
            raise HTTPException(status_code=400,
                                detail="Entry already exists in the database.") from exc
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_specimen_publication_by_id(specimen_publication_id: str):
        """
        It deletes a specimen_publication by id
        :param specimen_publication_id: str
        :type specimen_publication_id: str
        :return: The response is being returned.
        """
        try:
            SpecimenPublicationService.delete_specimen_publication_by_id(
                specimen_publication_id)
            return Response(content=f"Entry with ID: {specimen_publication_id} deleted.",
                            status_code=200)
        except SpecimenPublicationNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
