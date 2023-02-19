
"""
This module provides a database connection using SQLAlchemy and the `SessionLocal` object.
It also defines the `Base` object, which is used to define database models. The `get_db()`
function creates a database connection and then closes it when the function is done.

Variables:
- MYSQL_URL: The MySQL URL used to connect to the database.
- engine: The SQLAlchemy engine used to connect to the database.
- SessionLocal: The SQLAlchemy session maker used to create database sessions.
- Base: The SQLAlchemy declarative base used to define database models.

Functions:
- get_db(): The function used to create a database connection and close it when the function
  is done.

"""


from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.config import settings

if settings.USE_TEST_DB:
    db_name = settings.DB_NAME_TEST
else:
    db_name = settings.DB_NAME

MYSQL_URL = f"{settings.DB_HOST}://{settings.DB_USER}:{settings.DB_PASSWORD}" \
            f"@{settings.DB_HOSTNAME}:{settings.DB_PORT}/{db_name}"

engine = create_engine(MYSQL_URL, echo=True)

SessionLocal = sessionmaker(autocommit=False, autoflush=True, bind=engine)

Base = declarative_base()


def get_db():
    """
    It creates a database connection and then closes it when the function is done
    """
    database = SessionLocal()
    try:
        yield database
    finally:
        database.close()
