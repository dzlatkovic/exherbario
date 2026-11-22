from concurrent.futures import ThreadPoolExecutor
from hashlib import sha256
from pathlib import Path

from fastapi.testclient import TestClient
from sqlalchemy import URL, select

from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.chemistry.sample_links import new_link
from app.db import SessionLocal
from app.db.backup import backup_archive, restore_archive
from app.db.database import create_database_engine
from app.deposition.models import Deposition, DepositionFile, DepositionVersion
from app.deposition.verify_archive import verify_archive
from app.config import settings
from app.main import app
from app.specimen.models import Specimen
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import client
from app.tests.test_sqlite_deployment import sqlite_archive
from app.users.services import UserServices, signJWT


BASE_URL = "https://herbar.example.edu"


def headers_for(user):
    role = "super_user" if user.is_superuser else "classic_user"
    return {"Authorization": "Bearer " + signJWT(user.user_id, role)["access_token"]}


def test_publish_retries_corrections_and_withdrawal(sqlite_archive, tmp_path, monkeypatch):
    archive, engine = sqlite_archive
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE_URL + "/")
    curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
    owner = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
    other = UserServices.create_user("Other", "User", "other@example.org", "password")
    admin, author, outsider = map(headers_for, (curator, owner, other))
    assert client.post("/api/institutions", headers=admin,
                       json={"code": "exu", "name": "Example University"}).status_code == 201
    specimen = SpecimenFixtures.create_test_specimen()
    voucher_url = f"/api/specimen/{specimen.specimen_id}"
    with SessionLocal() as db:
        study = Study(owner_id=owner.user_id, title="Test study", description="Private study notes")
        db.add(study)
        db.flush()
        sample = LabSample(study_id=study.id, code="V-1", plant_part="leaf", material_state="air-dried",
                           collection_notes="Private site details")
        db.add(sample)
        db.flush()
        db.add(new_link(sample.id, db.get(Specimen, specimen.specimen_id), None, "collected_alongside"))
        batch = Preparation(sample_id=sample.id, batch_code="B-1", kind="essential_oil",
                            method_reference="Test method reference", yield_percent=0.5)
        db.add(batch)
        db.commit()
        study_id, batch_id, sample_id = study.id, batch.id, sample.id

    source = b"\xef\xbb\xbffeature,value,confidence\r\nA,100,annotated\r\n"
    imported = client.post(f"/api/chemistry/preparations/{batch_id}/profiles", headers=author,
                           data={"run_code": "Run", "analytical_method": "Test method",
                                 "technique": "GC-MS", "run_metadata": '{"polarity_class": "non-polar"}', "measurement_basis": "peak_area_percent", "unit": "%"},
                           files={"file": ("source.csv", source, "text/csv")})
    assert imported.status_code == 201, imported.text
    profile_id = imported.json()["id"]

    drafts = "/api/depositions"
    metadata = {
        "institution_name": "Example University", "title": "Voucher profile",
        "description": "Approved description", "license": "CC BY 4.0",
        "rights_statement": "Credit the depositor.", "contributors": [{"name": "F. Scientist", "role": "analyst"}],
        "profile_ids": [profile_id],
    }
    created = client.post(drafts, headers=author, json={"institution": "exu"})
    assert created.status_code == 201, created.text
    root = created.json()
    path = f"{drafts}/{root['id']}"
    preview_url = f"{path}/draft/preview"
    assert client.get(preview_url, headers=author).status_code == 409
    assert client.get(f"{path}/draft", headers=outsider).status_code == 404
    edited = client.put(f"{path}/draft", headers=author,
                        json={**metadata, "expected_revision": root["draft_revision"]})
    assert edited.status_code == 200, edited.text
    pending = client.get(preview_url, headers=author).json()["releases"]
    assert ([item["id"] for item in pending["studies"]], [item["id"] for item in pending["runs"]],
            [item["id"] for item in pending["vouchers"]]) == ([study_id], [profile_id], [specimen.specimen_id])
    for route, payload in (
        (f"{voucher_url}/visibility", {"is_public": True, "public_location": "withheld"}),
        (f"/api/chemistry/studies/{study_id}/visibility", {"is_public": True}),
        (f"/api/chemistry/profiles/{profile_id}/visibility", {"is_public": True}),
    ):
        assert client.put(route, headers=admin, json=payload).status_code == 200
    first_preview = client.get(preview_url, headers=author)
    assert first_preview.status_code == 200, first_preview.text
    preview = first_preview.json()
    first_url = preview["snapshot"]["url"]
    assert first_url.startswith(BASE_URL + "/api/depositions/public/EXU/")
    assert preview["snapshot"]["schema_version"] == 6
    assert preview["snapshot"]["identifier"] == first_url.replace("/api/depositions/public/", "/depositions/")
    assert [voucher["id"] for voucher in preview["snapshot"]["vouchers"]] == [specimen.specimen_id]
    assert client.get(first_url).status_code == 404
    first_page = first_url.replace("/api/depositions/public/", "/depositions/")
    assert client.get(first_page).status_code == 404
    selected = preview["snapshot"]["profiles"][0]
    assert selected["sample"]["id"] == sample_id
    assert [(link["id"], link["role"]) for link in selected["sample"]["vouchers"]] == [
        (specimen.specimen_id, "collected_alongside")]
    assert selected["sample"]["vouchers"][0]["redetermined_since_linking"] is False
    assert selected["sample"]["material_state"] == "air-dried"
    assert selected["preparation"]["method_reference"] == "Test method reference"
    assert preview["snapshot"]["vouchers"][0]["location"] is None
    assert "Private site details" not in first_preview.text
    assert selected["file"]["sha256"] == sha256(source).hexdigest()
    file_url = selected["file"]["url"]
    assert client.get(file_url).status_code == 404
    other_draft = client.post(drafts, headers=outsider, json={"institution": "EXU", **metadata}).json()
    assert client.get(f"{drafts}/{other_draft['id']}/draft/preview", headers=admin).status_code == 409

    def approval(preview_data):
        return {key: preview_data[key] for key in ("draft_revision", "snapshot_sha256")}

    publish = f"{path}/publish"
    assert client.post(publish, headers=author, json=approval(preview)).status_code == 403
    assert client.put("/api/specimen/update-specimen", headers=admin, params={"specimen_id": specimen.specimen_id},
                      json={"subnomen": "Approved determination"}).status_code == 200
    assert client.post(publish, headers=admin, json=approval(preview)).status_code == 409
    preview = client.get(preview_url, headers=admin).json()

    with engine.begin() as connection:
        connection.exec_driver_sql(
            "CREATE TRIGGER fail_snapshot_file BEFORE INSERT ON deposition_file "
            "BEGIN SELECT RAISE(ABORT, 'simulated file failure'); END"
        )
    failure = TestClient(app, raise_server_exceptions=False).post(publish, headers=admin, json=approval(preview))
    assert failure.status_code == 500
    assert client.get(first_url).status_code == 404
    with SessionLocal() as db:
        assert db.get(Deposition, root["id"]).draft_revision == preview["draft_revision"]
        assert db.scalars(select(DepositionVersion)).all() == []
        assert db.scalars(select(DepositionFile)).all() == []
    with engine.begin() as connection:
        connection.exec_driver_sql("DROP TRIGGER fail_snapshot_file")

    def submit():
        return client.post(publish, headers=admin, json=approval(preview))

    with ThreadPoolExecutor(max_workers=2) as workers:
        pending = [workers.submit(submit) for _ in range(2)]
        replies = [future.result(timeout=15) for future in pending]
    assert [reply.status_code for reply in replies] == [200, 200]
    assert replies[0].json() == replies[1].json()
    published = client.get(first_url).json()
    assert published["snapshot"] == preview["snapshot"]
    assert published["snapshot"]["contributors"] == metadata["contributors"]
    assert published["snapshot"]["license"] == metadata["license"]
    page = client.get(first_page)
    assert page.status_code == 200
    for value in ("Test method reference", "Collected alongside the voucher", "CC BY 4.0",
                  "F. Scientist", "Citation", "Download version ZIP", "source.csv"):
        assert value in page.text
    assert "Private site details" not in page.text
    archive_url = f"{first_url}/archive.zip"
    bundle = client.get(archive_url)
    assert bundle.status_code == 200 and bundle.headers["content-type"] == "application/zip"
    assert bundle.headers["X-HERBAR-Snapshot-SHA256"] == published["snapshot_sha256"]
    bundle_path = tmp_path / "published-v1.zip"
    bundle_path.write_bytes(bundle.content)
    assert verify_archive(bundle_path, published["snapshot_sha256"])["identity"]["version"] == 1

    with SessionLocal() as db:
        original = Path(db.get(Profile, profile_id).source_path)
    original.write_bytes(b"changed live file")
    assert client.get(file_url).content == source
    assert client.get(file_url).headers["X-HERBAR-SHA256"] == sha256(source).hexdigest()
    original.write_bytes(source)
    assert client.put("/api/specimen/update-specimen", headers=admin, params={"specimen_id": specimen.specimen_id},
                      json={"subnomen": "Revised determination"}).status_code == 200
    old_determination = client.get(first_url).json()["snapshot"]["vouchers"][0]["determination"]
    assert old_determination["name_as_recorded"] == "Approved determination"

    doi_url = f"{path}/versions/1/article-doi"
    assert client.put(doi_url, headers=author, json={"doi": "10.0000/Example"}).status_code == 403
    for _ in range(2):
        assert client.put(doi_url, headers=admin, json={"doi": "10.0000/Example"}).status_code == 200
    linked = client.get(first_url).json()
    assert linked["article_dois"] == ["10.0000/example"]
    assert linked["snapshot_sha256"] == published["snapshot_sha256"]
    assert client.get(archive_url).content == bundle.content
    assert "https://doi.org/10.0000/example" in client.get(first_page).text

    assert client.put(f"{path}/draft", headers=author, json={**metadata, "expected_revision": None}).status_code == 409
    correction = client.put(f"{path}/draft", headers=author, json={
        **metadata, "expected_revision": None, "title": "Corrected title", "correction_reason": "Correct the title",
    })
    assert correction.status_code == 200, correction.text
    corrected = client.get(preview_url, headers=admin).json()
    assert client.post(publish, headers=admin, json=approval(corrected)).status_code == 200
    second_url = corrected["snapshot"]["url"]
    second_page = second_url.replace("/api/depositions/public/", "/depositions/")
    second = client.get(second_url).json()["snapshot"]
    assert second["supersedes"] == first_url
    assert second["vouchers"][0]["determination"]["name_as_recorded"] == "Revised determination"
    assert second["profiles"][0]["sample"]["vouchers"][0]["redetermined_since_linking"] is True
    superseded = client.get(first_url).json()
    assert superseded["status"] == "superseded" and superseded["snapshot"] == published["snapshot"]
    assert "A newer version is available" in client.get(first_page).text
    assert "Correct the title" in client.get(second_page).text

    withdrawal_url = f"{path}/versions/1/withdraw"
    reason = {"reason": "Replace the published version with its correction."}
    first_notice = client.post(withdrawal_url, headers=admin, json=reason)
    assert first_notice.status_code == 200
    assert client.post(withdrawal_url, headers=admin, json=reason).json() == first_notice.json()
    tombstone = client.get(first_url)
    assert tombstone.status_code == 410 and tombstone.json()["withdrawal"]["reason"] == reason["reason"]
    assert tombstone.json()["article_dois"] == linked["article_dois"]
    assert "snapshot" not in tombstone.json()
    assert client.get(file_url).status_code == 410
    assert client.get(archive_url).status_code == 410
    notice_page = client.get(first_page)
    assert notice_page.status_code == 410
    assert reason["reason"] in notice_page.text
    assert "Download version ZIP" not in notice_page.text
    assert client.get(second_url).status_code == 200
    assert submit().json() == replies[0].json()

    with SessionLocal() as db:
        assert len(db.scalars(select(DepositionVersion)).all()) == 2
        assert len(db.scalars(select(DepositionFile)).all()) == 2
    engine.dispose()
    snapshot = backup_archive(archive / "herbar.db", archive / "images", tmp_path / "deposition-backup")
    restored = restore_archive(snapshot, tmp_path / "restored-deposition")
    restored_engine = create_database_engine(URL.create("sqlite", database=str(restored / "herbar.db")))
    with monkeypatch.context() as patch:
        patch.setitem(SessionLocal.kw, "bind", restored_engine)
        patch.chdir(restored)
        try:
            assert client.get(second_url).json()["snapshot"] == second
            assert client.get(second["profiles"][0]["file"]["url"]).content == source
            assert client.get(first_url).json() == tombstone.json()
        finally:
            restored_engine.dispose()
