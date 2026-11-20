import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime
from hashlib import sha256
from io import BytesIO
from os import environ
from types import SimpleNamespace
from pathlib import Path
from threading import Event, local
from uuid import uuid4

import pytest
from PIL import Image
from sqlalchemy import MetaData, Table, URL, select

from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.db import SessionLocal
from app.db.backup import backup_archive, restore_archive
from app.db.database import create_database_engine
from app.deposition.models import Deposition
from app.field_loc.models import FieldLoc
from app.field_loc.repository import FieldLocRepository
from app.image.models import Image as ImageRecord
from app.specimen.models import Revision, ScientificCorrection, Specimen
from app.specimen.schemas import SpecimenSchemaUpdate
from app.specimen.services import SpecimenService
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import TestingSessionLocal, client
from app.users.services import UserServices
from app.visibility_preview import preview
from app.weather.models import Weather


@pytest.fixture
def sqlite_archive(tmp_path, monkeypatch):
    archive = tmp_path / "archive"
    archive.mkdir()
    database = archive / "herbar.db"
    url = URL.create("sqlite", database=str(database))
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    subprocess.run(
        [sys.executable, "-m", "alembic", "upgrade", "head"],
        cwd=Path(__file__).resolve().parents[2], check=True, timeout=30,
    )
    database_engine = create_database_engine(url)
    monkeypatch.setitem(SessionLocal.kw, "bind", database_engine)
    monkeypatch.setitem(TestingSessionLocal.kw, "bind", database_engine)
    monkeypatch.chdir(archive)
    try:
        yield archive, database_engine
    finally:
        database_engine.dispose()


def test_concurrent_specimen_edits_record_each_previous_identification(sqlite_archive):
    from sqlalchemy import event

    _, database_engine = sqlite_archive
    specimen = SpecimenFixtures.create_test_specimen()
    first_locked = Event()
    second_started = Event()
    allow_first_edit = Event()
    worker = local()

    @event.listens_for(database_engine, "before_cursor_execute")
    def signal_second_attempt(_connection, _cursor, statement, _parameters, _context, _many):
        if statement == "BEGIN IMMEDIATE" and getattr(worker, "first", None) is False:
            second_started.set()

    @event.listens_for(database_engine, "after_cursor_execute")
    def pause_first_edit(_connection, _cursor, statement, _parameters, _context, _many):
        if statement == "BEGIN IMMEDIATE" and getattr(worker, "first", None) is True:
            first_locked.set()
            assert allow_first_edit.wait(timeout=10)

    def edit(name, first):
        worker.first = first
        updated = SpecimenService.update_specimen(
            specimen.specimen_id, SpecimenSchemaUpdate(subnomen=name), specimen.collected_by,
        )
        return updated.subnomen

    with database_engine.connect() as first_connection, database_engine.connect() as second_connection:
        assert first_connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1
        assert second_connection.exec_driver_sql("PRAGMA foreign_keys").scalar_one() == 1

    with ThreadPoolExecutor(max_workers=2) as workers:
        first = workers.submit(edit, "First determination", True)
        try:
            assert first_locked.wait(timeout=10)
            second = workers.submit(edit, "Second determination", False)
            assert second_started.wait(timeout=10)
            assert not second.done()
        finally:
            allow_first_edit.set()
        assert first.result(timeout=12) == "First determination"
        assert second.result(timeout=12) == "Second determination"

    current = SpecimenService.read_specimen_by_id(specimen.specimen_id)
    assert current.subnomen == "Second determination"
    with SessionLocal() as db:
        history = db.query(Revision).filter_by(specimen_id=specimen.specimen_id).all()
        assert sorted(entry.prev_subnomen for entry in history) == sorted([
            specimen.subnomen, "First determination",
        ])


def test_sqlite_and_image_backup_restores_a_specimen_through_the_api(sqlite_archive, tmp_path, monkeypatch):
    archive, database_engine = sqlite_archive
    specimen = SpecimenFixtures.create_test_specimen()
    admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
    login = client.post("/api/users/login", json={"email": admin.email, "password": "password"})
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    image = BytesIO()
    Image.new("RGB", (4, 4), "green").save(image, "JPEG")
    upload = client.post(
        "/api/image/upload-image", headers=headers,
        params={"specimen_id": specimen.specimen_id, "image_type": "herbarium"},
        files={"file": ("voucher.jpg", image.getvalue(), "image/jpeg")},
    )
    assert upload.status_code == 200, upload.text
    assert upload.json()["sha256"] == sha256(image.getvalue()).hexdigest()
    photo_url = f"/api/image/{upload.json()['image_id']}"
    voucher_url = f"/api/specimen/{specimen.specimen_id}"
    assert client.put(f"{photo_url}/visibility", headers=headers, json={"is_public": True}).status_code == 200
    assert client.put(f"{voucher_url}/visibility", headers=headers,
                      json={"is_public": True, "public_location": "region"}).status_code == 200

    revised = client.put(
        "/api/specimen/update-specimen", headers=headers,
        params={"specimen_id": specimen.specimen_id},
        json={"subnomen": "Updated voucher determination"},
    )
    assert revised.status_code == 200, revised.text
    with SessionLocal() as db:
        study = Study(owner_id=admin.user_id, title="Synthetic study", description="")
        db.add(study)
        db.flush()
        sample = LabSample(study_id=study.id, specimen_id=specimen.specimen_id, code="Sample",
                           plant_part="leaf", collection_event="Synthetic site",
                           voucher_relationship="collected_alongside")
        db.add(sample)
        db.flush()
        preparation = Preparation(sample_id=sample.id, batch_code="Batch",
                                  kind="essential_oil", method_reference="Synthetic reference")
        db.add(preparation)
        db.commit()
        preparation_id = preparation.id
    source = b"\xef\xbb\xbffeature,value,confidence\r\nA,100,annotated\r\n"
    imported = client.post(f"/api/chemistry/preparations/{preparation_id}/profiles", headers=headers,
                           data={"run_code": "Run", "analytical_method": "Synthetic method",
                                 "measurement_basis": "peak_area_percent", "unit": "%"},
                           files={"file": ("source.csv", source, "text/csv")})
    assert imported.status_code == 201, imported.text
    download = f"/api/chemistry/profiles/{imported.json()['id']}/source"
    source_path, = (archive / "files").glob("*.csv")
    source_path.write_bytes(b"changed")
    assert client.get(download, headers=headers).status_code == 409
    with pytest.raises(ValueError, match="Chemistry profile .* SHA-256 mismatch"):
        backup_archive(archive / "herbar.db", archive / "images", tmp_path / "invalid-backup")
    assert not (tmp_path / "invalid-backup").exists()
    source_path.write_bytes(source)

    database_engine.dispose()
    snapshot = backup_archive(archive / "herbar.db", archive / "images", tmp_path / "backup")
    restored = restore_archive(snapshot, tmp_path / "restored")
    with pytest.raises(FileExistsError):
        restore_archive(snapshot, restored)

    restored_engine = create_database_engine(URL.create("sqlite", database=str(restored / "herbar.db")))
    monkeypatch.setitem(SessionLocal.kw, "bind", restored_engine)
    monkeypatch.chdir(restored)
    try:
        detail = client.get(f"/api/specimen/{specimen.specimen_id}")
        assert detail.status_code == 200
        assert detail.json()["subnomen"] == "Updated voucher determination"
        photo = client.get(detail.json()["photos"][0]["content_url"])
        assert photo.status_code == 200
        assert client.get(f"{photo_url}/original", headers=headers).content == image.getvalue()
        downloaded = client.get(download, headers=headers)
        assert downloaded.content == source
        assert downloaded.headers["X-HERBAR-SHA256"] == sha256(source).hexdigest()
        history = client.get(f"/api/specimen/{specimen.specimen_id}/revisions")
        assert history.json()[0]["previous_subnomen"] == specimen.subnomen
    finally:
        restored_engine.dispose()
    (snapshot / "files" / source_path.name).unlink()
    restore = subprocess.run(
        [sys.executable, "-m", "app.db.backup", "restore", str(snapshot), str(tmp_path / "invalid-restore")],
        cwd=Path(__file__).resolve().parents[2], capture_output=True, text=True, encoding="utf-8",
        env={**environ, "PYTHONIOENCODING": "utf-8"}, timeout=30,
    )
    assert restore.returncode == 1
    assert "Referenced file is missing" in restore.stderr
    assert imported.json()["id"] in restore.stderr
    assert not (tmp_path / "invalid-restore").exists()
    with (restored / "herbar.db").open("ab") as database:
        database.write(b"changed after the snapshot")
    with pytest.raises(ValueError, match="Snapshot database failed SHA-256 verification"):
        restore_archive(restored, tmp_path / "modified-db")


def test_collection_provenance_on_upgraded_sqlite(tmp_path, monkeypatch):
    archive = tmp_path / "upgrade"
    archive.mkdir()
    url = URL.create("sqlite", database=str(archive / "herbar.db"))
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    project = Path(__file__).resolve().parents[2]

    def upgrade(revision):
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", revision],
                       cwd=project, check=True, timeout=30)

    upgrade("0003")
    engine = create_database_engine(url)
    monkeypatch.setitem(SessionLocal.kw, "bind", engine)
    monkeypatch.setitem(TestingSessionLocal.kw, "bind", engine)

    def legacy_field_loc(repository, country, region, locality, altitude, habitat, gps_lat, gps_long, **_):
        # Write the location as the 0003 schema stores it; the current model has later columns.
        table = Table("field_loc", MetaData(), autoload_with=repository.db.connection())
        field_loc_id = str(uuid4())
        repository.db.execute(table.insert().values(
            field_loc_id=field_loc_id, country=country, region=region, locality=locality,
            altitude=altitude, habitat=habitat, gps_lat=gps_lat, gps_long=gps_long,
        ))
        repository.db.commit()
        return SimpleNamespace(field_loc_id=field_loc_id)

    monkeypatch.setattr(FieldLocRepository, "create_field_loc", legacy_field_loc)
    try:
        specimen_data = SpecimenFixtures.create_test_specimen_object()
        specimen_id = str(uuid4())
        image_id = str(uuid4())
        admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
        with engine.begin() as connection:
            old_metadata = MetaData()
            specimens = Table("specimen", old_metadata, autoload_with=connection)
            images = Table("image", old_metadata, autoload_with=connection)
            revisions = Table("revision", old_metadata, autoload_with=connection)
            values = specimen_data.model_dump(exclude_none=True)
            values["subnomen"] = "Earlier redetermination"
            connection.execute(specimens.insert().values(specimen_id=specimen_id, **values))
            connection.execute(images.insert().values(
                image_id=image_id, specimen_id=specimen_id, file_path="images/archived.jpg",
            ))
            revision_id = str(uuid4())
            connection.execute(revisions.insert().values(
                revision_id=revision_id, specimen_id=specimen_id, revised_by=admin.user_id,
                prev_taxon_id=specimen_data.taxon_id, prev_subnomen=specimen_data.subnomen,
                timestamp=datetime(2025, 1, 1),
            ))
        with SessionLocal() as db:
            db.add(Weather(specimen_id, 20, 40, 0, 2, 90))
            db.commit()
        study_id, sample_id, preparation_id, profile_id = [str(uuid4()) for _ in range(4)]
        with engine.begin() as connection:
            connection.execute(Study.__table__.insert().values(
                id=study_id, owner_id=admin.user_id, title="Synthetic study",
                description="", is_public=True,
            ))
            connection.execute(LabSample.__table__.insert().values(
                id=sample_id, study_id=study_id, specimen_id=specimen_id, code="Sample",
                plant_part="leaf", collection_event="Synthetic site", voucher_relationship="collected_alongside",
            ))
            connection.execute(Preparation.__table__.insert().values(
                id=preparation_id, sample_id=sample_id, batch_code="Batch",
                kind="essential_oil", method_reference="Synthetic reference",
            ))
            connection.execute(Profile.__table__.insert().values(
                id=profile_id, preparation_id=preparation_id, run_code="Run",
                analytical_method="Synthetic method", measurement_basis="peak_area_percent", unit="%",
                source_name="fixture.csv", source_csv="feature,value,confidence\nA,100,annotated",
                is_public=True,
            ))

        with engine.connect() as connection:
            assert preview(connection) == {
                "vouchers_withheld": 1, "photo_records_withheld": 1,
                "public_studies_withheld": 1, "public_profiles_withheld": 1,
            }
            assert connection.execute(select(specimens.c.specimen_id)).scalar_one() == specimen_id

        upgrade("0004")
        upgrade("0005")
        upgrade("0006")
        upgrade("head")
        with engine.connect() as connection:
            assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
        with SessionLocal() as db:
            specimen = db.get(Specimen, specimen_id)
            assert specimen.reg_no == specimen_data.reg_no
            assert specimen.accession is None and specimen.holding_type is None
            assert specimen.collector_name is None and specimen.collected_by == specimen_data.collected_by
            assert not specimen.is_public and specimen.public_location == "withheld"
            image = db.get(ImageRecord, image_id)
            assert not image.is_public and image.file_path == "images/archived.jpg" and image.sha256 is None
            assert image.specimen_id == specimen_id
            assert db.get(Revision, revision_id).prev_subnomen == specimen_data.subnomen
            assert db.get(Study, study_id).is_public
            legacy = db.get(Profile, profile_id)
            assert legacy.is_public and legacy.source_path is None and legacy.source_sha256 is None
            assert db.get(LabSample, sample_id).specimen_id == specimen_id
            assert db.scalars(select(Deposition)).all() == []
            assert db.scalars(select(ScientificCorrection)).all() == []
        assert client.get(f"/api/specimen/{specimen_id}").status_code == 404
        assert client.get(f"/api/image/{image_id}/content").status_code == 404
        assert client.get(f"/api/chemistry/public/studies/{study_id}").status_code == 404
        assert client.get(f"/api/chemistry/public/profiles/{profile_id}").status_code == 404

        login = client.post("/api/users/login", json={"email": admin.email, "password": "password"})
        headers = {"Authorization": "Bearer " + login.json()["access_token"]}
        legacy_download = client.get(f"/api/chemistry/profiles/{profile_id}/source", headers=headers)
        assert legacy_download.content == b"feature,value,confidence\nA,100,annotated"
        assert legacy_download.headers["X-HERBAR-Source-Fidelity"] == "legacy-reconstructed"
        assert "X-HERBAR-SHA256" not in legacy_download.headers
        images = archive / "images"
        images.mkdir()
        Image.new("RGB", (4, 4), "blue").save(images / "archived.jpg", "JPEG")
        snapshot = backup_archive(archive / "herbar.db", images, tmp_path / "snapshot")
        legacy_photo = snapshot / "images" / "archived.jpg"
        legacy_photo.write_bytes(b"changed after the snapshot")
        with pytest.raises(ValueError, match="referenced files differ from the manifest: images/archived.jpg"):
            restore_archive(snapshot, tmp_path / "corrupt")
        assert not (tmp_path / "corrupt").exists()
        legacy_photo.write_bytes((images / "archived.jpg").read_bytes())
        (snapshot / "manifest.json").unlink()
        with pytest.raises(ValueError, match="Snapshot has no manifest.json"):
            restore_archive(snapshot, tmp_path / "legacy-restore")
        with pytest.warns(UserWarning, match="Legacy snapshot has no manifest"):
            restored = restore_archive(snapshot, tmp_path / "legacy-restore", allow_legacy=True)
        assert (restored / "manifest.json").is_file()
        assert (restored / "images" / "archived.jpg").read_bytes() == legacy_photo.read_bytes()
        site = {"field_loc_id": specimen.field_loc_id}
        voucher = {"specimen_id": specimen.specimen_id}
        assert client.delete("/api/field-locations/delete-field-loc", params=site, headers=headers).status_code == 409
        assert client.delete("/api/specimen/delete-specimen", params=voucher, headers=headers).status_code == 409
        site_update = "/api/field-locations/update-field-loc"
        assert client.put(site_update, params=site, headers=headers, json={"gps_lat": 0}).status_code == 400
        response = client.put(site_update, params=site, headers=headers,
                              json={"gps_lat": 0, "correction_reason": "Checked field notebook"})
        assert response.status_code == 200, response.text
        specimen_update = "/api/specimen/update-specimen"
        response = client.put(specimen_update, params=voucher, headers=headers, json={
            "collection_date": "2010-01-02",
            "subnomen": "Corrected determination",
            "correction_reason": "Checked original voucher label",
        })
        assert response.status_code == 200, response.text

        with SessionLocal() as db:
            kept = db.get(Specimen, specimen.specimen_id)
            assert kept.field_loc_id == specimen.field_loc_id
            assert db.get(FieldLoc, specimen.field_loc_id).gps_lat == 0
            assert db.scalar(select(Weather.specimen_id)) == specimen.specimen_id
            correction = db.scalar(select(ScientificCorrection).filter_by(specimen_id=specimen.specimen_id))
            assert correction.actor_id == admin.user_id
            assert correction.timestamp is not None
            assert correction.reason == "Checked original voucher label"
            assert correction.old_values == {
                "collection_date": "2010-01-01", "subnomen": "Earlier redetermination",
            }
            assert correction.new_values == {
                "collection_date": "2010-01-02", "subnomen": "Corrected determination",
            }
            site_correction = db.scalar(select(ScientificCorrection).filter_by(field_loc_id=specimen.field_loc_id))
            assert site_correction.actor_id == admin.user_id
            assert site_correction.old_values == {"gps_lat": 43}
            assert site_correction.new_values == {"gps_lat": 0}
            assert {row.prev_subnomen for row in db.scalars(select(Revision))} == {
                specimen_data.subnomen, "Earlier redetermination",
            }
    finally:
        engine.dispose()


def test_failed_correction_preserves_voucher_and_history(sqlite_archive):
    _, engine = sqlite_archive
    specimen = SpecimenFixtures.create_test_specimen()
    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TRIGGER reject_correction BEFORE INSERT ON scientific_correction "
            "BEGIN SELECT RAISE(ABORT, 'simulated correction write failure'); END"
        )
    admin = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
    login = client.post("/api/users/login", json={"email": admin.email, "password": "password"})
    headers = {"Authorization": "Bearer " + login.json()["access_token"]}
    voucher = {"specimen_id": specimen.specimen_id}
    response = client.put("/api/specimen/update-specimen", params=voucher, headers=headers, json={
        "subnomen": "Corrected determination",
        "correction_reason": "Checked original label",
    })
    assert response.status_code == 500
    with SessionLocal() as db:
        assert db.get(Specimen, specimen.specimen_id).subnomen == specimen.subnomen
        assert db.scalars(select(Revision)).all() == []
        assert db.scalars(select(ScientificCorrection)).all() == []
        db.add(Weather(specimen.specimen_id, 20, 40, 0, 2, 90))
        db.commit()
    assert client.delete("/api/specimen/delete-specimen", params=voucher, headers=headers).status_code == 409
    with SessionLocal() as db:
        assert db.scalar(select(Weather.specimen_id)) == specimen.specimen_id
