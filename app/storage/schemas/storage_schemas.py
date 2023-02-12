from pydantic import BaseModel, UUID4


class StorageSchema(BaseModel):
    storage_id: UUID4
    room: str
    shelf: str
    box: str

    class Config:
        orm_mode = True


class StorageSchemaIn(BaseModel):
    room: str
    shelf: str
    box: str

    class Config:
        orm_mode = True
