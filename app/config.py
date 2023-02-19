"""This module contains the Settings class."""

from pydantic import BaseSettings


class Settings(BaseSettings):
    """
    A class that defines the settings of the application.
    Attributes:
        DB_HOST (str): The hostname of the database server
        DB_HOSTNAME (str): The name of the database
        DB_PORT (int): The port number of the database
        DB_USER (str): The username for connecting to the database
        DB_PASSWORD (str): The password for connecting to the database
        DB_NAME (str): The name of the database
        USER_SECRET (str): The secret key for generating JWT tokens
        ALGORITHM (str): The algorithm for generating JWT tokens

    Config:
        env_file (str): The path to the file containing the environment variables
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

    class Config:
        """
        The configuration settings for the Settings class.

        Attributes:
            env_file (str): The path to the file containing the environment variables
        """
        env_file = './.env'


settings = Settings()
