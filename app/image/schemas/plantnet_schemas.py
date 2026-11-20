from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, UUID4


class Organs(Enum):
    auto = "auto"
    leaf = "leaf"
    flower = "flower"
    fruit = "fruit"
    bark = "bark"


class PlantNetResultSchema(BaseModel):
    result_id: UUID4
    image_id: str
    best_match: str
    gbif_id: str
    score: float
    timestamp: datetime

    model_config = ConfigDict(from_attributes=True)


class PlantNetResultSchemaIn(BaseModel):
    image_id: str
    best_match: str
    gbif_id: str
    score: float

    model_config = ConfigDict(from_attributes=True)
