from app.specimen.models import Specimen
from app.specimen.exceptions import SpecimenNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class SpecimenRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_specimen(self, reg_no: str, collection_date: str, reg_date: str,
                        family: str, genus: str, species: str, subnomen: str,
                        field_loc_id: str, storage_id: str, photos_id: str,
                        collected_by: str, verified_by: str):
        try:
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
