from pydantic import BaseModel, UUID4
from datetime import date


class SpecimenSchema(BaseModel):
    specimen_id: UUID4
    reg_no: str
    collection_date: date
    reg_date: date
    family: str
    genus: str
    species: str
    subnomen: str
    field_loc_id: str
    storage_id: str
    photos_id: str
    collected_by: str
    verified_by: str

    class Config:
        orm_mode = True


class SpecimenSchemaIn(BaseModel):
    reg_no: str
    collection_date: str
    reg_date: str
    family: str
    genus: str
    species: str
    subnomen: str
    field_loc_id: str
    storage_id: str
    photos_id: str
    collected_by: str
    verified_by: str

    class Config:
        orm_mode = True
