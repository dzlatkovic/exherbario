from datetime import datetime
from sqlalchemy import Column, String, ForeignKey, Float, DateTime

from app.db import Base, new_id


class PlantNetResult(Base):
    """
    Represents a result from the PlantNet image recognition API.
    """

    __tablename__ = "plantnet_result"
    result_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    image_id = Column(String(50), ForeignKey("image.image_id"))
    best_match = Column(String(150))
    gbif_id = Column(String(20))
    score = Column(Float)
    timestamp = Column(DateTime, default=datetime.utcnow)

    def __init__(self, image_id: str, best_match: str, gbif_id: str, score: float):
        """
        Constructs a new PlantNetResult object.

        :param image_id: The ID of the image associated with the result.
        :param best_match: The scientific name of the best matching plant species.
        :param gbif_id: The ID of the matching species in the Global
                        Biodiversity Information Facility (GBIF) database.
        :param score: The confidence score of the matching result (0.0 to 1.0).
        """
        self.image_id = image_id
        self.best_match = best_match
        self.gbif_id = gbif_id
        self.score = score
        self.timestamp = datetime.utcnow()
