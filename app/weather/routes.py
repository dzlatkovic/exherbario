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
