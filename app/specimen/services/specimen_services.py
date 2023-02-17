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

    @staticmethod
    def get_specimens_per_year():
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                specimens_per_year = repository.get_specimens_per_year()
                return [{'year': year, 'count': count}
                        for year, count in specimens_per_year]
        except Exception as e:
            raise e

    @staticmethod
    def get_specimens_per_user():
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_specimens_per_user()
        except Exception as e:
            raise e

    @staticmethod
    def get_specimens_per_region():
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_specimens_per_region()
        except Exception as e:
            raise e

    @staticmethod
    def count_specimens():
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.count_specimens()
        except Exception as e:
            raise e

    @staticmethod
    def get_gps_for_genus(genus: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_gps_for_genus(genus)
        except Exception as e:
            raise e

    @staticmethod
    def get_last_specimens():
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_last_specimens()
        except Exception as e:
            raise e

    @staticmethod
    def get_herbarium_label(reg_no: str):
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                if not repository.read_specimen_by_reg_num(reg_no):
                    raise SpecimenExceptionRegNo(message="No such specimen in the database",
                                                 code=400)
                return repository.get_herbarium_label(reg_no)
        except Exception as e:
            raise e
