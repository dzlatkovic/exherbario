from sqlalchemy.orm import Session

from app.weather.exceptions import (DataAlreadyExistException,
                                    SpecimenDoesNotExistException)
from app.specimen.models import Specimen
from app.weather.models import Weather


class WeatherRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_weather_data(self, specimen_id: str, mean_temperature: float, humidity: float,
                            precipitation: float, wind_speed: float, wind_direction: float):
        if not self.db.query(Specimen).filter_by(specimen_id=specimen_id).first():
            raise SpecimenDoesNotExistException(
                code=404,
                message=f"Specimen with id: {specimen_id} does not exist in the Specimen Table."
            )
        if self.db.query(Weather).filter_by(specimen_id=specimen_id).first():
            raise DataAlreadyExistException(
                code=400,
                message=f"Weather data for specimen with id: {specimen_id} already exists in the Weather table."
            )
        try:
            weather_data = Weather(specimen_id=specimen_id,
                                   mean_temperature=mean_temperature,
                                   humidity=humidity,
                                   precipitation=precipitation,
                                   wind_speed=wind_speed,
                                   wind_direction=wind_direction)
            self.db.add(weather_data)
            self.db.commit()
            self.db.refresh(weather_data)
            return weather_data
        except Exception as error:
            raise error
