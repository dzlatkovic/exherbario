import subprocess
import sys
from concurrent.futures import ThreadPoolExecutor
from io import BytesIO
from pathlib import Path
from threading import Event, local

import pytest
from PIL import Image
from sqlalchemy import URL

from app.db import SessionLocal
from app.db.backup import backup_archive, restore_archive
from app.db.database import create_database_engine
from app.specimen.models import Revision
from app.specimen.schemas import SpecimenSchemaUpdate
from app.specimen.services import SpecimenService
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import TestingSessionLocal, client
from app.users.services import UserServices


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

    revised = client.put(
        "/api/specimen/update-specimen", headers=headers,
        params={"specimen_id": specimen.specimen_id},
        json={"subnomen": "Updated voucher determination"},
    )
    assert revised.status_code == 200, revised.text
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
        assert photo.content == image.getvalue()
        history = client.get(f"/api/specimen/{specimen.specimen_id}/revisions")
        assert history.json()[0]["previous_subnomen"] == specimen.subnomen
    finally:
        restored_engine.dispose()
