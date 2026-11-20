from datetime import date
from enum import Enum

from pydantic import BaseModel, UUID4


class ImageType(Enum):
    field = "field"
    herbarium = "herbarium"
    macro = "macro"
    microscope = "microscope"


class ImageSchema(BaseModel):
    image_id: UUID4
    specimen_id: str
    image_type: ImageType
    file_path: str
    width: int
    height: int
    upload_date: date
    sha256: str | None = None

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class ImageSchemaIn(BaseModel):
    specimen_id: str
    image_type: ImageType
    file_path: str
    width: int
    height: int
    upload_date: date
    sha256: str | None = None

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
