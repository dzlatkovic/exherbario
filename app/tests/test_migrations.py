from pathlib import Path

import pytest
import sqlalchemy as sa
from alembic import op
from alembic.autogenerate import compare_metadata
from alembic.config import Config
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory

import app.main  # Registers the ORM metadata for schema comparison.
from app.db import Base


def migrations():
    config = Config(Path(__file__).resolve().parents[2] / "alembic.ini")
    return ScriptDirectory.from_config(config)


def test_chemistry_upgrade_resumes_after_creating_the_study_table(monkeypatch):
    scripts = migrations()
    baseline = scripts.get_revision("0001").module
    chemistry = scripts.get_revision("0002").module
    with sa.create_engine("sqlite://").begin() as connection:
        context = MigrationContext.configure(connection)
        with Operations.context(context):
            baseline.upgrade()
            create_table = op.create_table

            def interrupt_after_study(name, *definition, **options):
                if name == "chemistry_pca":
                    raise RuntimeError("interrupted upgrade")
                return create_table(name, *definition, **options)

            with monkeypatch.context() as patch:
                patch.setattr(op, "create_table", interrupt_after_study)
                with pytest.raises(RuntimeError, match="interrupted upgrade"):
                    chemistry.upgrade()

            metadata = sa.MetaData()
            users = sa.Table("users", metadata, autoload_with=connection)
            studies = sa.Table("chemistry_study", metadata, autoload_with=connection)
            connection.execute(users.insert().values(user_id="owner"))
            connection.execute(studies.insert().values(
                id="study", owner_id="owner", title="Existing study",
                description="", is_public=False,
            ))

            chemistry.upgrade()
            assert connection.scalar(sa.select(studies.c.title)) == "Existing study"
            scripts.get_revision("0003").module.upgrade()
            scripts.get_revision("0004").module.upgrade()
            assert not compare_metadata(context, Base.metadata)


def test_chemistry_upgrade_reports_an_incompatible_existing_table():
    scripts = migrations()
    with sa.create_engine("sqlite://").begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            scripts.get_revision("0001").module.upgrade()
            op.create_table("chemistry_study", sa.Column("unexpected_column", sa.String(50)))

            with pytest.raises(RuntimeError, match="Existing table chemistry_study does not match"):
                scripts.get_revision("0002").module.upgrade()
