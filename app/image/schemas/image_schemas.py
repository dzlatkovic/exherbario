from datetime import date

from pydantic import BaseModel, UUID4, Json


class ImageSchema(BaseModel):
    image_id: UUID4
    specimen_id: str
    file_path: str
    width: int
    height: int
    upload_date: date

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class ImageSchemaIn(BaseModel):
    specimen_id: str
    file_path: str
    width: int
    height: int
    upload_date: date

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
