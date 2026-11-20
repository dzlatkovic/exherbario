from datetime import date
from enum import Enum

from pydantic import BaseModel, ConfigDict, UUID4


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

    model_config = ConfigDict(from_attributes=True)


class ImageSchemaIn(BaseModel):
    specimen_id: str
    image_type: ImageType
    file_path: str
    width: int
    height: int
    upload_date: date
    sha256: str | None = None

    model_config = ConfigDict(from_attributes=True)
