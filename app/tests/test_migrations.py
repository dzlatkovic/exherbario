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
            scripts.get_revision("0005").module.upgrade()
            scripts.get_revision("0006").module.upgrade()
            scripts.get_revision("0007").module.upgrade()
            scripts.get_revision("0008").module.upgrade()
            scripts.get_revision("0009").module.upgrade()
            scripts.get_revision("0010").module.upgrade()
            assert not compare_metadata(context, Base.metadata)


def test_chemistry_upgrade_reports_an_incompatible_existing_table():
    scripts = migrations()
    with sa.create_engine("sqlite://").begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            scripts.get_revision("0001").module.upgrade()
            op.create_table("chemistry_study", sa.Column("unexpected_column", sa.String(50)))

            with pytest.raises(RuntimeError, match="Existing table chemistry_study does not match"):
                scripts.get_revision("0002").module.upgrade()


def test_sample_voucher_migration_converts_samples_and_guards_downgrade():
    scripts = migrations()
    with sa.create_engine("sqlite://").begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            for revision in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008", "0009"):
                scripts.get_revision(revision).module.upgrade()
            metadata = sa.MetaData()
            tables = {name: sa.Table(name, metadata, autoload_with=connection) for name in (
                "users", "taxonomy", "specimen", "chemistry_study", "chemistry_sample")}
            connection.execute(tables["users"].insert().values(user_id="owner"))
            connection.execute(tables["taxonomy"].insert().values(
                taxon_id="t1", taxon_name="Achillea millefolium", gbif_key="3120060", taxon_rank="species"))
            for specimen_id in ("v1", "v2"):
                connection.execute(tables["specimen"].insert().values(
                    specimen_id=specimen_id, taxon_id="t1", subnomen="Achillea millefolium L."))
            connection.execute(tables["chemistry_study"].insert().values(
                id="study", owner_id="owner", title="Study", description="", is_public=False))
            for sample_id, part in (("a", " Leaves"), ("b", "needles and twigs")):
                connection.execute(tables["chemistry_sample"].insert().values(
                    id=sample_id, study_id="study", specimen_id="v1", code=sample_id, plant_part=part,
                    collection_event=f"Site {sample_id}", voucher_relationship="sampled_from_voucher"))

            scripts.get_revision("0010").module.upgrade()
            assert connection.execute(sa.text(
                "SELECT id, plant_part, plant_part_note, collection_notes FROM chemistry_sample ORDER BY id")).all() == [
                ("a", "leaf", None, "Site a"), ("b", "other", "needles and twigs", "Site b")]
            assert connection.execute(sa.text(
                "SELECT sample_id, specimen_id, role, taxon_name_at_link, name_at_link, determination_recorded "
                "FROM chemistry_sample_voucher ORDER BY sample_id")).all() == [
                ("a", "v1", "sampled_from_voucher", "Achillea millefolium", "Achillea millefolium L.", "at_migration"),
                ("b", "v1", "sampled_from_voucher", "Achillea millefolium", "Achillea millefolium L.", "at_migration")]

            connection.execute(sa.text(
                "INSERT INTO chemistry_sample_voucher (sample_id, specimen_id, role, linked_at, determination_recorded) "
                "VALUES ('a', 'v2', 'same_population', '2026-11-20 00:00:00', 'at_link')"))
            with pytest.raises(RuntimeError, match="exactly one voucher per lab sample"):
                scripts.get_revision("0010").module.downgrade()
            connection.execute(sa.text("DELETE FROM chemistry_sample_voucher WHERE specimen_id = 'v2'"))
            connection.execute(sa.text("UPDATE chemistry_sample SET material_state = 'fresh' WHERE id = 'a'"))
            with pytest.raises(RuntimeError, match="remove recorded sample provenance"):
                scripts.get_revision("0010").module.downgrade()
            connection.execute(sa.text("UPDATE chemistry_sample SET material_state = NULL"))

            scripts.get_revision("0010").module.downgrade()
            assert connection.execute(sa.text(
                "SELECT id, specimen_id, plant_part, collection_event, voucher_relationship "
                "FROM chemistry_sample ORDER BY id")).all() == [
                ("a", "v1", "leaf", "Site a", "sampled_from_voucher"),
                ("b", "v1", "needles and twigs", "Site b", "sampled_from_voucher")]
            assert not sa.inspect(connection).has_table("chemistry_sample_voucher")
