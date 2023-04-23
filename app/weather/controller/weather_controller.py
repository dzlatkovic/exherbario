from fastapi import HTTPException

from app.specimen.exceptions import SpecimenNotFoundException
from app.weather.exceptions import (DataAlreadyExistException,
                                    SpecimenDoesNotExistException,
                                    UnsuccessfulAPIRequestException, MissingGPSException)
from app.weather.services import WeatherService
from app.weather.schemas import WeatherSchemaIn, WeatherSchema


class WeatherController:
    @staticmethod
    def create_weather_data(weather: WeatherSchemaIn):
        try:
            return WeatherService.save_weather_data(weather)
        except (DataAlreadyExistException,
                SpecimenDoesNotExistException,
                UnsuccessfulAPIRequestException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def download_weather_data(specimen_id: str):
        try:
            return WeatherService.fetch_and_save_weather_data(specimen_id)
        except (UnsuccessfulAPIRequestException,
                MissingGPSException,
                SpecimenNotFoundException,
                DataAlreadyExistException,
                SpecimenDoesNotExistException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
