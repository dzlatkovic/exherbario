from pydantic import BaseModel, ConfigDict, UUID4


class WeatherSchema(BaseModel):
    weather_id: UUID4
    specimen_id: str
    mean_temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_direction: float

    model_config = ConfigDict(from_attributes=True)


class WeatherSchemaIn(BaseModel):
    specimen_id: str
    mean_temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_direction: float

    model_config = ConfigDict(from_attributes=True)
