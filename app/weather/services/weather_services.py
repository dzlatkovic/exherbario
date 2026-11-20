from typing import Tuple

import requests
from app.db import SessionLocal
from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.models import Specimen
from app.specimen.services import SpecimenService
from app.weather.exceptions import (UnsuccessfulAPIRequestException,
                                    MissingGPSException,
                                    MissingWeatherDataException)
from app.weather.repository import WeatherRepository
from app.weather.schemas import WeatherSchemaIn

API_ENDPOINT = 'https://archive-api.open-meteo.com/v1/archive'


class WeatherService:
    @staticmethod
    def save_weather_data(weather: WeatherSchemaIn):
        try:
            with SessionLocal() as db:
                repository = WeatherRepository(db)
                return repository.create_weather_data(weather.specimen_id,
                                                      weather.mean_temperature,
                                                      weather.humidity,
                                                      weather.precipitation,
                                                      weather.wind_speed,
                                                      weather.wind_direction)
        except Exception as error:
            raise error

    @staticmethod
    def fetch_weather_data_from_api(specimen_id, longitude, latitude, timestamp) -> WeatherSchemaIn:
        try:
            date = timestamp.strftime("%Y-%m-%d")
            response = requests.get(API_ENDPOINT, params={
                'latitude': latitude,
                'longitude': longitude,
                'start_date': date,
                'end_date': date,
                'hourly': 'relativehumidity_2m',
                "daily": "temperature_2m_mean,precipitation_sum,windspeed_10m_max,winddirection_10m_dominant",
                "timezone": "Europe/Berlin",
                "windspeed_unit": "ms"
            }, timeout=(5, 20))

            if response.status_code == 200:
                weather_data = response.json()
                weather_object_in = WeatherSchemaIn(
                    specimen_id=specimen_id,
                    mean_temperature=weather_data["daily"]["temperature_2m_mean"][0],
                    humidity=weather_data["hourly"]["relativehumidity_2m"][12],
                    precipitation=weather_data["daily"]["precipitation_sum"][0],
                    wind_speed=weather_data["daily"]["windspeed_10m_max"][0],
                    wind_direction=weather_data["daily"]["winddirection_10m_dominant"][0]
                )
                return weather_object_in
            else:
                raise UnsuccessfulAPIRequestException(code=response.status_code, message=response.text)
        except Exception as error:
            raise error

    @staticmethod
    def get_lat_long_from_specimen(specimen_id) -> Tuple[float, float]:
        try:
            with SessionLocal() as db:
                specimen = db.query(Specimen).filter_by(specimen_id=specimen_id).first()
                if not specimen:
                    raise SpecimenNotFoundException(code=404, message="Specimen was not found.")
                field_loc = specimen.field_loc
                if field_loc and field_loc.gps_lat is not None and field_loc.gps_long is not None:
                    return field_loc.gps_lat, field_loc.gps_long
                else:
                    raise MissingGPSException(code=400, message="GPS data was not found.")
        except Exception as error:
            raise error

    @staticmethod
    def fetch_and_save_weather_data(specimen_id: str):
        try:
            specimen = SpecimenService.read_specimen_by_id(specimen_id)
            if specimen.collection_date is None:
                raise MissingWeatherDataException(code=400, message="Collection date is required to download weather.")
            latitude, longitude = WeatherService.get_lat_long_from_specimen(specimen_id)
            weather_object_in = WeatherService.fetch_weather_data_from_api(specimen_id,
                                                                           longitude,
                                                                           latitude,
                                                                           specimen.collection_date)
            return WeatherService.save_weather_data(weather_object_in)
        except Exception as error:
            raise error

    @staticmethod
    def read_weather_by_specimen_id(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = WeatherRepository(db)
                if not db.query(Specimen).filter_by(specimen_id=specimen_id).first():
                    raise SpecimenNotFoundException(
                        code=404,
                        message=f"Specimen with ID: {specimen_id} does not exist."
                    )
                weather_data = repository.read_weather_by_specimen_id(specimen_id)
                if weather_data is None:
                    raise MissingWeatherDataException(
                        code=404,
                        message=f"Weather data for specimen with ID: {specimen_id} does not exist."
                    )
                return weather_data
        except Exception as error:
            raise error

    @staticmethod
    def delete_weather_data(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = WeatherRepository(db)
                if not db.query(Specimen).filter_by(specimen_id=specimen_id).first():
                    raise SpecimenNotFoundException(
                        code=404,
                        message=f"Specimen with ID: {specimen_id} does not exist."
                    )
                weather_data = repository.read_weather_by_specimen_id(specimen_id)
                if weather_data is None:
                    raise MissingWeatherDataException(
                        code=404,
                        message=f"Weather data for specimen with ID: {specimen_id} does not exist."
                    )
                return repository.delete_weather_data(specimen_id)
        except Exception as error:
            raise error
