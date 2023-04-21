from fastapi import APIRouter
from app.weather.controller import WeatherController
from app.weather.schemas import WeatherSchema, WeatherSchemaIn

weather_router = APIRouter(prefix="/api/weather", tags=["Weather"])


@weather_router.post("/create-weather_data", response_model=WeatherSchema)
def create_new_photos(weather: WeatherSchemaIn):
    return WeatherController.create_weather_data(weather)
