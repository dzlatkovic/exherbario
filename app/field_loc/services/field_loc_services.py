from app.field_loc.models import FieldLoc
from app.db import SessionLocal
from app.field_loc.repository import FieldLocRepository


class FieldLocService:

    @staticmethod
    def create_new_field_loc(country: str, region: str, locality: str, altitude: int,
                             habitat: str, gps_lat: float, gps_long: float) -> FieldLoc:
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.create_field_loc(country, region, locality, altitude,
                                                   habitat, gps_lat, gps_long)
        except Exception as e:
            raise e

    @staticmethod
    def read_all_field_locations():
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.read_all_field_locations()
        except Exception as e:
            raise e

    @staticmethod
    def read_field_loc_by_id(field_loc_id: str):
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.read_field_loc_by_id(field_loc_id)
        except Exception as e:
            raise e

    @staticmethod
    def delete_field_loc_by_id(field_loc_id: str):
        try:
            with SessionLocal() as db:
                repository = FieldLocRepository(db)
                return repository.delete_field_loc(field_loc_id)
        except Exception as e:
            raise e
