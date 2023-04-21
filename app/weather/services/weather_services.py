from app.db import SessionLocal
from app.weather.repository import WeatherRepository
from app.weather.schemas import WeatherSchemaIn


class WeatherService:
    @staticmethod
    def create_weather_data(weather: WeatherSchemaIn):
        try:
            with SessionLocal() as db:
                repository = WeatherRepository(db)
                return repository.create_weather_data(weather.specimen_id,
                                                      weather.mean_temperature,
                                                      weather.humidity,
                                                      weather.precipitation,
                                                      weather.wind_speed,
                                                      weather.wind_direction)
        except ValueError as error:
            raise error
        except Exception as error:
            raise error
