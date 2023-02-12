from app.field_loc.models import FieldLoc
from app.field_loc.exceptions import FieldLocNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class FieldLocRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_field_loc(self, country: str, region: str, locality: str, altitude: int,
                         habitat: str, gps_lat: float, gps_long: float):
        try:
            field_loc = FieldLoc(country, region, locality, altitude, habitat, gps_lat, gps_long)
            self.db.add(field_loc)
            self.db.commit()
            self.db.refresh(field_loc)
            return field_loc
        except IntegrityError as e:
            raise e
        except Exception as e:
            raise e

    def read_all_field_locations(self):
        courses = self.db.query(FieldLoc).all()
        return courses

    def read_field_loc_by_id(self, field_loc_id: str):
        field_loc = self.db.query(FieldLoc).filter(FieldLoc.field_loc_id == field_loc_id).first()
        if field_loc is None:
            raise FieldLocNotFoundException(f"Location with provided ID: {field_loc_id} not found.", 400)
        return field_loc

    def delete_field_loc(self, field_loc_id: str):
        try:
            field_loc = self.db.query(FieldLoc).filter(FieldLoc.field_loc_id == field_loc_id).first()
            if field_loc is None:
                raise FieldLocNotFoundException(f"Location with provided ID: {field_loc_id} not found.", 400)
            self.db.delete(field_loc)
            self.db.commit()
            return True
        except Exception as e:
            raise e
