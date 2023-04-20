"""This module contains the Settings class."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    A class that defines the settings of the application.

    :param DB_HOST: The hostname of the database server.
    :type DB_HOST: str
    :param DB_HOSTNAME: The name of the database.
    :type DB_HOSTNAME: str
    :param DB_PORT: The port number of the database.
    :type DB_PORT: int
    :param DB_USER: The username for connecting to the database.
    :type DB_USER: str
    :param DB_PASSWORD: The password for connecting to the database.
    :type DB_PASSWORD: str
    :param DB_NAME: The name of the database.
    :type DB_NAME: str
    :param USER_SECRET: The secret key for generating JWT tokens.
    :type USER_SECRET: str
    :param ALGORITHM: The algorithm for generating JWT tokens.
    :type ALGORITHM: str
    :param DB_NAME_TEST: The name of the test database.
    :type DB_NAME_TEST: str
    :param USE_TEST_DB: A boolean flag indicating whether to use the test database.
    :type USE_TEST_DB: bool
    :param LATITUDE: The latitude value used in distance calculations.
    :type LATITUDE: float
    :param LONGITUDE: The longitude value used in distance calculations.
    :type LONGITUDE: float
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
