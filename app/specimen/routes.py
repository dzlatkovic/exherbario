from fastapi import APIRouter

from app.specimen.controller import SpecimenController
from app.specimen.schemas import SpecimenSchema, SpecimenSchemaIn

specimen_router = APIRouter(prefix="/api/specimen", tags=["Specimen"])


@specimen_router.post("/create-new-specimen", response_model=SpecimenSchema)
def create_new_specimen(specimen: SpecimenSchemaIn):
    return SpecimenController.create_new_specimen(reg_no=specimen.reg_no,
                                                  collection_date=specimen.collection_date,
                                                  reg_date=specimen.reg_date,
                                                  family=specimen.family,
                                                  genus=specimen.genus,
                                                  species=specimen.species,
                                                  subnomen=specimen.subnomen,
                                                  field_loc_id=specimen.field_loc_id,
                                                  storage_id=specimen.storage_id,
                                                  photos_id=specimen.photos_id,
                                                  collected_by=specimen.collected_by,
                                                  verified_by=specimen.verified_by)


@specimen_router.get("/get-specimen-by-id", response_model=SpecimenSchema)
def get_storage_by_id(specimen_id: str):
    return SpecimenController.get_specimen_by_id(specimen_id)


@specimen_router.delete("/delete-specimen")
def delete_specimen_by_id(specimen_id: str):
    return SpecimenController.delete_specimen_by_id(specimen_id)
