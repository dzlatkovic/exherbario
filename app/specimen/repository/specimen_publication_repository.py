"""This module contains the SpecimenPublicationRepository class."""


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.publication.models import Publication
from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.models import SpecimenPublication, Specimen


class SpecimenPublicationRepository:
    """
    A class that handles database operations for SpecimenPublication objects.
    """
    def __init__(self, db: Session):
        """
        Constructs a new instance of the SpecimenPublicationRepository
        class with the given database session
        :param db: The database session to use for database operations.
        :type db: sqlalchemy.orm.Session
        """
        self.db = db

    def create_specimen_publication(self, specimen_id: str, publication_id: str):
        """
        Creates a new SpecimenPublication object with the given specimen_id
        and publication_id, and saves it to the database
        :param specimen_id: The ID of the specimen to associate with the publication
        :type specimen_id: str
        :param publication_id: The ID of the publication to associate with the specimen
        :type publication_id: str
        :return: The newly created SpecimenPublication object
        :rtype: app.specimen.models.SpecimenPublication
        """
        if not self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first():
            raise ValueError(f"{specimen_id} is not a valid foreign key")
        if not self.db.query(Publication).filter(Publication.pub_id == publication_id).first():
            raise ValueError(f"{publication_id} is not a valid foreign key")
        try:
            specimen_publication = SpecimenPublication(specimen_id, publication_id)
            self.db.add(specimen_publication)
            self.db.commit()
            self.db.refresh(specimen_publication)
            return specimen_publication
        except IntegrityError as error:
            raise error

    def delete_specimen_publication_by_id(self, specimen_publication_id: str):
        """
        Deletes a SpecimenPublication object with the given specimen_publication_id
        from the database
        :param specimen_publication_id: The ID of the SpecimenPublication object to delete
        :type specimen_publication_id: str
        :return: True if the object was deleted, False otherwise
        :rtype: bool
        """
        try:
            specimen_publication = self.db.query(SpecimenPublication)\
                .filter(SpecimenPublication.specimen_publication_id
                        == specimen_publication_id).first()
            if specimen_publication is None:
                raise SpecimenPublicationNotFoundException(
                    code=400,
                    message=f"Entry with an ID {specimen_publication_id} not found.",
                )
            self.db.delete(specimen_publication)
            self.db.commit()
            return True
        except Exception as error:
            raise error
