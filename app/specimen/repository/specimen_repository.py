from app.field_loc.models import FieldLoc
from app.photos.models import Photos
from app.specimen.models import Specimen
from app.specimen.exceptions import SpecimenNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.storage.models import Storage
from app.users.models import User


class SpecimenRepository:

    def __init__(self, db: Session):
        self.db = db

    def validate_foreign_keys(self, field_loc_id: str, storage_id: str, photos_id: str,
                              collected_by: str, verified_by: str):
        """
        Check if provided foreign keys are valid
        :param field_loc_id: The ID of the field location to check
        :param storage_id: The ID of the storage to check
        :param photos_id: The ID of the photos to check
        :param collected_by: The ID of the collector to check
        :param verified_by: The ID of the verifier to check
        :raises ValueError: If any of the provided foreign keys are invalid
        """
        if field_loc_id:
            if not self.db.query(FieldLoc).filter(FieldLoc.field_loc_id
                                                  == field_loc_id).first():
                raise ValueError(f"Invalid field_loc_id: {field_loc_id}")
        if storage_id:
            if not self.db.query(Storage).filter(Storage.storage_id == storage_id).first():
                raise ValueError(f"Invalid storage_id: {storage_id}")
        if photos_id:
            if not self.db.query(Photos).filter(Photos.photos_id == photos_id).first():
                raise ValueError(f"Invalid photos_id: {photos_id}")
        if collected_by:
            if not self.db.query(User).filter(User.user_id == collected_by).first():
                raise ValueError(f"Invalid collected_by: {collected_by}")
        if verified_by:
            if not self.db.query(User).filter(User.user_id == verified_by).first():
                raise ValueError(f"Invalid verified_by: {verified_by}")

    def create_specimen(self, reg_no: str, collection_date: str, reg_date: str,
                        family: str, genus: str, species: str, subnomen: str,
                        field_loc_id: str, storage_id: str, photos_id: str,
                        collected_by: str, verified_by: str):
        if self.db.query(Specimen).filter_by(photos_id=photos_id).first():
            raise ValueError('A specimen with the same photos_id already exists in the database')
        try:
            self.validate_foreign_keys(field_loc_id, storage_id, photos_id, collected_by,
                                       verified_by)
            specimen = Specimen(reg_no, collection_date, reg_date, family,
                                genus, species, subnomen, field_loc_id, storage_id,
                                photos_id, collected_by, verified_by)
            self.db.add(specimen)
            self.db.commit()
            self.db.refresh(specimen)
            return specimen
        except IntegrityError as e:
            raise e
        except Exception as e:
            raise e

    def read_specimen_by_id(self, specimen_id: str):
        specimen = self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first()
        if specimen is None:
            raise SpecimenNotFoundException(f"Specimen with the provided ID: "
                                            f"{specimen_id} not found.", 400)
        return specimen

    def delete_specimen(self, specimen_id: str):
        try:
            specimen = self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first()
            if specimen is None:
                raise SpecimenNotFoundException(f"Specimen with provided ID: "
                                                f"{specimen_id} not found.", 400)
            self.db.delete(specimen)
            self.db.commit()
            return True
        except Exception as e:
            raise e

    def read_specimen_by_reg_num(self, reg_no: str):
        return self.db.query(Specimen).filter(Specimen.reg_no == reg_no).first()
