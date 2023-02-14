from app.specimen.models import Specimen
from app.db import SessionLocal
from app.specimen.repository import SpecimenRepository
from app.specimen.exceptions import SpecimenExceptionRegNo


class SpecimenService:

    @staticmethod
    def create_new_specimen(reg_no: str, collection_date: str, reg_date: str,
                            family: str, genus: str, species: str, subnomen: str,
                            field_loc_id: str, storage_id: str, photos_id: str,
                            collected_by: str, verified_by: str) -> SpecimenExceptionRegNo or Specimen:
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                publication = repository.read_specimen_by_reg_num(reg_no)
                if publication is None:
                    return repository.create_specimen(reg_no, collection_date, reg_date,
                                                      family, genus, species, subnomen,
                                                      field_loc_id, storage_id, photos_id,
                                                      collected_by, verified_by)
                raise SpecimenExceptionRegNo(message="Specimen already exists in the database.", code=400)
        except Exception as e:
            raise e

    @staticmethod
    def read_specimen_by_id(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.read_specimen_by_id(specimen_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_specimen_by_id(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.delete_specimen(specimen_id)
        except Exception as e:
            raise e
