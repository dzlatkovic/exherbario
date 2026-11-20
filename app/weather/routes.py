from fastapi import APIRouter, Depends
from app.weather.controller import WeatherController
from app.weather.schemas import WeatherSchema, WeatherSchemaIn
from app.users.controller import JWTBearer

weather_router = APIRouter(prefix="/api/weather", tags=["Weather"])


@weather_router.post("/create-weather_data", response_model=WeatherSchema,
                     dependencies=[Depends(JWTBearer("super_user"))])
def create_weather_data(weather: WeatherSchemaIn) -> WeatherSchema:
    return WeatherController.create_weather_data(weather)


@weather_router.post("/download-weather_data", response_model=WeatherSchema,
                     dependencies=[Depends(JWTBearer("super_user"))])
def download_weather_data(specimen_id: str) -> WeatherSchema:
    return WeatherController.download_weather_data(specimen_id)


@weather_router.get("/get-weather_data", dependencies=[Depends(JWTBearer())], response_model=WeatherSchema)
def get_weather_data_by_specimen_id(specimen_id: str) -> WeatherSchema:
    return WeatherController.get_weather_by_specimen_id(specimen_id)


@weather_router.delete("/delete-weather_data",
                       dependencies=[Depends(JWTBearer("super_user"))])
def delete_weather_data(specimen_id: str):
    return WeatherController.delete_weather_data(specimen_id)
