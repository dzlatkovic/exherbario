from datetime import datetime
from enum import Enum

from pydantic import BaseModel, UUID4


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

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class PlantNetResultSchemaIn(BaseModel):
    image_id: str
    best_match: str
    gbif_id: str
    score: float

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
