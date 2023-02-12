from pydantic import BaseModel, UUID4


class FieldLocSchema(BaseModel):
    field_loc_id: UUID4
    country: str
    region: str
    locality: str
    altitude: int
    habitat: str
    gps_lat: float
    gps_long: float

    class Config:
        orm_mode = True


class FieldLocSchemaIn(BaseModel):
    country: str
    region: str
    locality: str
    altitude: int
    habitat: str
    gps_lat: float
    gps_long: float

    class Config:
        orm_mode = True
