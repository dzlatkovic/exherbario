from fastapi import APIRouter
from app.weather.controller import WeatherController
from app.weather.schemas import WeatherSchema, WeatherSchemaIn

weather_router = APIRouter(prefix="/api/weather", tags=["Weather"])


@weather_router.post("/create-weather_data", response_model=WeatherSchema)
def create_weather_data(weather: WeatherSchemaIn) -> WeatherSchema:
    return WeatherController.create_weather_data(weather)


@weather_router.post("/download-weather_data", response_model=WeatherSchema)
def download_weather_data(specimen_id: str) -> WeatherSchema:
    return WeatherController.download_weather_data(specimen_id)


@weather_router.post("/get-weather_data", response_model=WeatherSchema)
def get_weather_data_by_specimen_id(specimen_id: str) -> WeatherSchema:
    return WeatherController.get_weather_by_specimen_id(specimen_id)


@weather_router.delete("/delete-weather_data")
def delete_weather_data(specimen_id: str):
    return WeatherController.delete_weather_data(specimen_id)
