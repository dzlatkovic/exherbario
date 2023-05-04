"""This module contains the SpecimenPublicationRepository class."""


from sqlalchemy.orm import Session

from app.specimen.models import Specimen, Revision
from app.specimen.schemas import RevisionSchemaIn
from app.taxonomy.models import Taxonomy
from app.users.models import User


class RevisionRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_revision(self, revision_data: RevisionSchemaIn):

        if not self.db.query(Specimen).filter(Specimen.specimen_id == revision_data.specimen_id).first():
            raise ValueError(f"{revision_data.specimen_id} is not a valid specimen foreign key")
        if not self.db.query(User).filter(User.user_id == revision_data.revised_by).first():
            raise ValueError(f"{revision_data.revised_by} is not a valid user foreign key")
        if not self.db.query(Taxonomy).filter(Taxonomy.taxon_id == revision_data.prev_taxon_id).first():
            raise ValueError(f"{revision_data.prev_taxon_id} is not a valid user taxon foreign key")
        try:
            revision = Revision(
                revised_by=revision_data.revised_by,
                specimen_id=revision_data.specimen_id,
                prev_taxon_id=revision_data.prev_taxon_id,
                prev_subnomen=revision_data.prev_subnomen
            )
            self.db.add(revision)
            self.db.commit()
            self.db.refresh(revision)
            return revision
        except Exception as error:
            raise error
