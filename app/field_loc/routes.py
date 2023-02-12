from fastapi import APIRouter

from app.field_loc.controller import FieldLocController
from app.field_loc.schemas import FieldLocSchema, FieldLocSchemaIn

field_loc_router = APIRouter(prefix="/api/field_locations", tags=["FieldLoc"])


@field_loc_router.post("/create-new-field-loc", response_model=FieldLocSchema)
def create_new_field_loc(field_loc: FieldLocSchemaIn):
    return FieldLocController.create_new_field_loc(country=field_loc.country, region=field_loc.region,
                                                   locality=field_loc.locality, altitude=field_loc.altitude,
                                                   habitat=field_loc.habitat, gps_lat=field_loc.gps_lat,
                                                   gps_long=field_loc.gps_long)


@field_loc_router.get("/get-all-field-locations", response_model=list[FieldLocSchema])
def get_all_field_locations():
    field_locations = FieldLocController.get_all_field_locations()
    return field_locations


@field_loc_router.get("/get-field-loc-by-id", response_model=FieldLocSchema)
def get_field_loc_by_id(field_loc_id: str):
    return FieldLocController.get_field_loc_by_id(field_loc_id)


@field_loc_router.delete("/delete-field-loc")
def delete_field_loc_by_id(field_loc_id: str):
    return FieldLocController.delete_field_loc_by_id(field_loc_id)
