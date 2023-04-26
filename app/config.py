"""This module contains the Settings class."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    A class that defines the settings of the application.

    :param DB_HOST: The hostname of the database server.
    :param DB_HOSTNAME: The name of the database.
    :param DB_PORT: The port number of the database.
    :param DB_USER: The username for connecting to the database.
    :param DB_PASSWORD: The password for connecting to the database.
    :param DB_NAME: The name of the database.
    :param USER_SECRET: The secret key for generating JWT tokens.
    :param ALGORITHM: The algorithm for generating JWT tokens.
    :param DB_NAME_TEST: The name of the test database.
    :param USE_TEST_DB: A boolean flag indicating whether to use the test database.
    :param LATITUDE: The latitude value used in distance calculations.
    :param TOKEN_DURATION: The expiration time of the JWT token
    :param LONGITUDE: The longitude value used in distance calculations.
    """
    DB_HOST: str
    DB_HOSTNAME: str
    DB_PORT: int
    DB_USER: str
    DB_PASSWORD: str
    DB_NAME: str
    USER_SECRET: str
    ALGORITHM: str
    DB_NAME_TEST: str
    USE_TEST_DB: bool
    TOKEN_DURATION: int
    LATITUDE: float
    LONGITUDE: float

    class Config:
        """
        The configuration settings for the Settings class.

        :param env_file: The path to the file containing the environment variables.
        :type env_file: str
        """
        env_file = './.env'


settings = Settings()
