"""Database configuration shared by the API, migrations, and tests."""

import sqlite3
from uuid import uuid4

from sqlalchemy import create_engine, event, make_url
from sqlalchemy.orm import declarative_base, sessionmaker

from app.config import settings


def create_database_engine(url, **options):
    database_url = make_url(url)
    if database_url.get_backend_name() == "sqlite":
        database_engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False, "timeout": 10,
                          "autocommit": sqlite3.LEGACY_TRANSACTION_CONTROL},
            hide_parameters=True,
            **options,
        )

        @event.listens_for(database_engine, "connect")
        def enforce_foreign_keys(connection, _):
            connection.execute("PRAGMA foreign_keys=ON").close()

        return database_engine

    raise ValueError("HERBAR stores its archive in SQLite. Set DATABASE_URL to a sqlite:/// path.")


DATABASE_URL = make_url(settings.DATABASE_URL)
engine = create_database_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
Base = declarative_base()


def new_id():
    return str(uuid4())


def get_db():
    with SessionLocal() as database:
        yield database


def lock_for_update(session, query):
    """Serialize SQLite writes before reading a row that is about to change."""
    if session.get_bind().dialect.name == "sqlite":
        connection = session.connection()
        if not connection.connection.driver_connection.in_transaction:
            connection.exec_driver_sql("BEGIN IMMEDIATE")
        return query.populate_existing()
    return query.populate_existing().with_for_update()
