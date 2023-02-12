from sqlalchemy import Column, String, Integer, Float
from uuid import uuid4

from app.db import Base


class FieldLoc(Base):
    __tablename__ = "field_loc"
    field_loc_id = Column(String(50), primary_key=True, default=uuid4, autoincrement=False)
    country = Column(String(20))
    region = Column(String(20))
    locality = Column(String(40))
    altitude = Column(Integer)
    habitat = Column(String(20))
    gps_lat = Column(Float)
    gps_long = Column(Float)

    def __init__(self, country: str, region: str, locality: str, altitude: int,
                 habitat: str, gps_lat: float, gps_long: float):
        self.country = country
        self.region = region
        self.locality = locality
        self.altitude = altitude
        self.habitat = habitat
        self.gps_lat = gps_lat
        self.gps_long = gps_long
