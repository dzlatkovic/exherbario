from fastapi import HTTPException, Response

from app.specimen.exceptions import SpecimenNotFoundException
from app.weather.exceptions import (DataAlreadyExistException,
                                    SpecimenDoesNotExistException,
                                    UnsuccessfulAPIRequestException,
                                    MissingGPSException,
                                    MissingWeatherDataException)
from app.weather.services import WeatherService
from app.weather.schemas import WeatherSchemaIn


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
                MissingWeatherDataException,
                SpecimenNotFoundException,
                DataAlreadyExistException,
                SpecimenDoesNotExistException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_weather_by_specimen_id(specimen_id: str):
        try:
            return WeatherService.read_weather_by_specimen_id(specimen_id)
        except (SpecimenNotFoundException, MissingWeatherDataException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_weather_data(specimen_id: str):
        try:
            WeatherService.delete_weather_data(specimen_id)
            return Response(content=f"Weather data for specimen with ID: "
                                    f"{specimen_id} deleted.", status_code=200)
        except (SpecimenNotFoundException, MissingWeatherDataException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
