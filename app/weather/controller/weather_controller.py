from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.weather.services import WeatherService
from app.weather.schemas import WeatherSchemaIn


class WeatherController:
    @staticmethod
    def create_weather_data(weather: WeatherSchemaIn):
        try:
            return WeatherService.create_weather_data(weather)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
