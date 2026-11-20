"""This module contains the Settings class."""

from pydantic_settings import BaseSettings, SettingsConfigDict


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
    :param PUBLIC_BASE_URL: Public origin of this instance, e.g. https://herbar.example.edu. Published
        deposition versions record absolute identifiers under it, so it must be set before publishing.
    :param ZENODO_URL: Zenodo instance used to mirror published versions and obtain dataset DOIs.
    :param ZENODO_TOKEN: Personal access token with deposit:write and deposit:actions scopes.
    """
    DATABASE_URL: str = "sqlite:///./herbar.db"
    USER_SECRET: str
    ALGORITHM: str
    TOKEN_DURATION: int
    LATITUDE: float
    LONGITUDE: float
    PLANTNET_API_KEY: str
    PUBLIC_BASE_URL: str = ""
    ZENODO_URL: str = "https://zenodo.org"
    ZENODO_TOKEN: str = ""

    # Read environment variables, then ./.env. Unrelated keys in .env are ignored, as before.
    model_config = SettingsConfigDict(env_file="./.env", extra="ignore")


settings = Settings()
