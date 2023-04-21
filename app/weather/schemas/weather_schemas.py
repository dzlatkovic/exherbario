from pydantic import BaseModel, UUID4


class WeatherSchema(BaseModel):
    weather_id: UUID4
    specimen_id: str
    mean_temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_direction: float

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True


class WeatherSchemaIn(BaseModel):
    specimen_id: str
    mean_temperature: float
    humidity: float
    precipitation: float
    wind_speed: float
    wind_direction: float

    class Config:
        """
        Configuration for Pydantic schema to work with ORM
        """
        orm_mode = True
