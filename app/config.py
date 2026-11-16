"""This module contains the Settings class."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    A class that defines the settings of the application.

    :param DATABASE_URL: The database connection used by the API and Alembic.
    :param USER_SECRET: The secret key for generating JWT tokens.
    :param ALGORITHM: The algorithm for generating JWT tokens.
    :param TOKEN_DURATION: The expiration time of the JWT token
    :param LATITUDE: The latitude value used in distance calculations.
    :param LONGITUDE: The longitude value used in distance calculations.
    :param PLANTNET_API_KEY: Private key for Pl@ntNet API.
    """
    DATABASE_URL: str = "sqlite:///./herbar.db"
    USER_SECRET: str
    ALGORITHM: str
    TOKEN_DURATION: int
    LATITUDE: float
    LONGITUDE: float
    PLANTNET_API_KEY: str

    class Config:
        """
        The configuration settings for the Settings class.

        :param env_file: The path to the file containing the environment variables.
        :type env_file: str
        """
        env_file = './.env'


settings = Settings()
