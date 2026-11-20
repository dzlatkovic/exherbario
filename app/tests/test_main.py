"""Run each test with its own empty database tables."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import inspect
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.db import Base, SessionLocal
from app.db.database import create_database_engine
from app.main import app

TestingSessionLocal = sessionmaker()
client = TestClient(app)


def create_test_engine():
    return create_database_engine("sqlite://", poolclass=StaticPool)


class TestClass:
    def setup_method(self):
        self.engine = create_test_engine()
        try:
            if inspect(self.engine).get_table_names():
                raise RuntimeError("The test database must be empty.")
            Base.metadata.create_all(bind=self.engine)
        except Exception:
            self.engine.dispose()
            raise
        self.original_bind = SessionLocal.kw["bind"]
        SessionLocal.configure(bind=self.engine)
        TestingSessionLocal.configure(bind=self.engine)

    def teardown_method(self):
        SessionLocal.configure(bind=self.original_bind)
        TestingSessionLocal.configure(bind=None)
        try:
            Base.metadata.drop_all(bind=self.engine)
        finally:
            self.engine.dispose()


def test_only_sqlite_archives_are_supported():
    with pytest.raises(ValueError, match="SQLite"):
        create_database_engine("postgresql://herbar@localhost/herbar")
