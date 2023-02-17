"""
This module defines the PublicationAuthorsRepository class,
which provides methods for managing publication author mappings in the database.
"""
from collections import defaultdict

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.publication.exceptions import (PublicationAuthorsNotFoundException,
                                        EntryAlreadyExistsException)
from app.publication.models import PublicationAuthors, Publication
from app.specimen.models import SpecimenPublication, Specimen
from app.users.models import User


class PublicationAuthorsRepository:
    """
    Repository class for managing publication authors in the database.
    """

    def __init__(self, db: Session):
        """
        Initializes a new PublicationAuthorsRepository object
        :param db: Database session object.
        """
        self.db = db

    def create_publication_authors(self, user_id: str, publication_id: str):
        """
        Creates a new publication author mapping with the provided information
        :param user_id: Unique identifier for the user associated with the publication
        :param publication_id: Unique identifier for the publication associated with the user
        :return: PublicationAuthors object representing the created mapping
        """
        if not self.db.query(User).filter(User.user_id == user_id).first():
            raise ValueError(f"{user_id} is not a valid foreign key")
        if not self.db.query(Publication).filter(Publication.pub_id == publication_id).first():
            raise ValueError(f"{publication_id} is not a valid foreign key")
        try:
            publication_authors = PublicationAuthors(user_id, publication_id)
            self.db.add(publication_authors)
            self.db.commit()
            self.db.refresh(publication_authors)
            return publication_authors
        except IntegrityError as error:
            if "Duplicate entry" in str(error):
                raise EntryAlreadyExistsException(
                    code=400,
                    message="Entry already exists in the database") from error
            raise error

    def delete_publication_authors_by_id(self, publication_authors_id: str):
        """
        Deletes a publication author mapping by ID
        :param publication_authors_id: ID of the publication author mapping to delete
        :return: True if the mapping was successfully deleted
        """
        try:
            publication_authors = self.db.query(PublicationAuthors).filter(
                PublicationAuthors.publication_authors_id
                == publication_authors_id).first()
            if publication_authors is None:
                raise PublicationAuthorsNotFoundException(
                    code=400,
                    message=f"Entry with an ID {publication_authors_id} not found",
                )
            self.db.delete(publication_authors)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def get_publication_report(self):
        report = {}
        specimen_publications = self.db.query(SpecimenPublication).all()
        for sp in specimen_publications:
            specimen = self.db.query(Specimen).filter_by(specimen_id=sp.specimen_id).first()
            publication = self.db.query(Publication).filter_by(pub_id=sp.publication_id).first()
            if publication.doi not in report:
                report[publication.doi] = {"authors": [], "species": []}
            authors = self.db.query(User).join(PublicationAuthors).filter_by(
                publication_id=publication.pub_id).all()
            for author in authors:
                report[publication.doi]["authors"].append(f"{author.name} {author.surname}")
            species = f"{specimen.genus} {specimen.species}"
            if species not in report[publication.doi]["species"]:
                report[publication.doi]["species"].append(species)
        return report
