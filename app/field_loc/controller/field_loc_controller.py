from app.field_loc.services import FieldLocService
from app.field_loc.exceptions import FieldLocExceptionCode, FieldLocNotFoundException

from fastapi import HTTPException, Response


class FieldLocController:

    @staticmethod
    def create_new_field_loc(country: str, region: str, locality: str, altitude: int,
                             habitat: str, gps_lat: float, gps_long: float):
        try:
            course = FieldLocService.create_new_field_loc(country, region, locality, altitude,
                                                          habitat, gps_lat, gps_long)
            return course
        except FieldLocExceptionCode as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_all_field_locations():
        field_locations = FieldLocService.read_all_field_locations()
        return field_locations

    @staticmethod
    def get_field_loc_by_id(field_loc_id: str):
        try:
            field_loc = FieldLocService.read_field_loc_by_id(field_loc_id)
            return field_loc
        except FieldLocNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_field_loc_by_id(field_loc_id: str):
        try:
            FieldLocService.delete_course_by_id(field_loc_id)
            return Response(content=f"Field location with provided ID: "
                                    f"{field_loc_id} deleted.", status_code=200)
        except FieldLocNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
