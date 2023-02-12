from pydantic import BaseModel, UUID4


class PhotosSchema(BaseModel):
    photos_id: UUID4
    field_photo: str
    specimen_photo: str

    class Config:
        orm_mode = True


class PhotosSchemaIn(BaseModel):
    field_photo: str
    specimen_photo: str

    class Config:
        orm_mode = True
