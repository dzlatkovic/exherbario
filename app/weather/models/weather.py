from sqlalchemy import Column, String, Float, ForeignKey
from sqlalchemy.orm import relationship

from app.db import Base, new_id


class Weather(Base):
    __tablename__ = "weather"
    weather_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    specimen_id = Column(String(50), ForeignKey("specimen.specimen_id"), unique=True)
    mean_temperature = Column(Float)
    humidity = Column(Float)
    precipitation = Column(Float)
    wind_speed = Column(Float)
    wind_direction = Column(Float)

    specimen = relationship("Specimen", back_populates="weather")

    def __init__(self, specimen_id: str, mean_temperature: float, humidity: float,
                 precipitation: float, wind_speed: float, wind_direction: float):
        self.specimen_id = specimen_id
        self.mean_temperature = mean_temperature
        self.humidity = humidity
        self.precipitation = precipitation
        self.wind_speed = wind_speed
        self.wind_direction = wind_direction
