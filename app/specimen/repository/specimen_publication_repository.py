from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.specimen.exceptions.specimen_publication_exceptions import SpecimenPublicationNotFoundException
from app.specimen.models import SpecimenPublication


class SpecimenPublicationRepository:
    def __init__(self, db: Session):
        self.db = db

    def create_specimen_publication(self, specimen_id: str, publication_id: str):
        try:
            specimen_publication = SpecimenPublication(specimen_id, publication_id)
            self.db.add(specimen_publication)
            self.db.commit()
            self.db.refresh(specimen_publication)
            return specimen_publication
        except IntegrityError as e:
            raise e

    def delete_specimen_publication_by_id(self, specimen_publication_id: str):
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
        except Exception as e:
            raise e
