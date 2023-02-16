"""This module contains the SpecimenPublicationService class."""


from app.db import SessionLocal
from app.specimen.repository import SpecimenPublicationRepository


class SpecimenPublicationService:
    """
    A class that provides high-level operations on SpecimenPublication objects.
    """
    @staticmethod
    def create_new_specimen_publication(specimen_id: str, publication_id: str):
        """
        Creates a new SpecimenPublication object with the given
        specimen_id and publication_id, and saves it to the database
        :param specimen_id: The ID of the specimen to associate with the publication
        :type specimen_id: str
        :param publication_id: The ID of the publication to associate with the specimen
        :type publication_id: str
        :return: The newly created SpecimenPublication object
        :rtype: app.specimen.models.SpecimenPublication
        :raises: Exception: If an error occurs while creating the SpecimenPublication object
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenPublicationRepository(db)
                return repository.create_specimen_publication(specimen_id, publication_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_specimen_publication_by_id(specimen_publication_id: str):
        """
        Deletes a SpecimenPublication object with the given specimen_publication_id from
         the database
        :param specimen_publication_id: The ID of the SpecimenPublication object to delete
        :type specimen_publication_id: str
        :return: True if the object was deleted, False otherwise
        :rtype: bool
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenPublicationRepository(db)
                return repository.delete_specimen_publication_by_id(specimen_publication_id)
        except Exception as error:
            raise error
