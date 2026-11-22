"""Persistent identifiers, institution registry, voucher-only depositions and dataset DOIs."""

from hashlib import sha256
from types import SimpleNamespace
from zipfile import ZipFile

import pytest
import sqlalchemy as sa
from alembic.migration import MigrationContext
from alembic.operations import Operations

from app.config import settings
from app.deposition.archive import build_archive, manifest_for, snapshot_digest
from app.deposition.mirror_zenodo import mirror, zenodo_license
from app.deposition.verify_archive import verify_archive
from app.specimen.tests.unittests.test_specimen_repo import TestSpecimenRepo as SpecimenFixtures
from app.tests import client
from app.tests.test_depositions import BASE_URL, headers_for
from app.tests.test_migrations import migrations
from app.tests.test_sqlite_deployment import sqlite_archive  # noqa: F401  (pytest fixture)
from app.users.services import UserServices

VALID_ORCID = "0000-0002-1825-0097"


@pytest.fixture
def accounts(sqlite_archive, monkeypatch):  # noqa: F811
    monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE_URL)
    curator = UserServices.create_super_user("Curator", "Example", "curator@example.org", "password")
    owner = UserServices.create_user("Lab", "Owner", "lab@example.org", "password")
    return SimpleNamespace(curator=curator, admin=headers_for(curator), author=headers_for(owner),
                           archive=sqlite_archive[0])


def test_institution_registry_ties_codes_to_external_registries(accounts):
    entry = {"code": "beo", "name": "Natural History Museum, Belgrade",
             "index_herbariorum_code": "beo", "ror_id": "https://ror.org/05pn4ss79"}
    assert client.post("/api/institutions", headers=accounts.author, json=entry).status_code == 403
    created = client.post("/api/institutions", headers=accounts.admin, json=entry)
    assert created.status_code == 201, created.text
    assert created.json() == {"code": "BEO", "name": entry["name"], "index_herbariorum_code": "BEO",
                              "ror": "https://ror.org/05pn4ss79"}
    assert client.post("/api/institutions", headers=accounts.admin, json=entry).json() == created.json()
    assert client.post("/api/institutions", headers=accounts.admin,
                       json={**entry, "name": "Another name"}).status_code == 409
    assert client.post("/api/institutions", headers=accounts.admin,
                       json={**entry, "code": "OTHER"}).status_code == 409
    assert client.post("/api/institutions", headers=accounts.admin,
                       json={"code": "BAD", "name": "Bad", "ror_id": "not-a-ror"}).status_code == 422
    assert client.get("/api/institutions").json() == [created.json()]
    unregistered = client.post("/api/depositions", headers=accounts.author, json={"institution": "NOPE"})
    assert unregistered.status_code == 409 and "Register institution code NOPE" in unregistered.text


def test_voucher_only_deposition_receives_citable_identifiers_and_a_dataset_doi(accounts, tmp_path, monkeypatch):
    admin, author = accounts.admin, accounts.author
    assert client.post("/api/institutions", headers=admin, json={
        "code": "EXU", "name": "Example University", "ror_id": "05pn4ss79"}).status_code == 201
    specimen = SpecimenFixtures.create_test_specimen()
    updated = client.put("/api/specimen/update-specimen", headers=admin, params={"specimen_id": specimen.specimen_id},
                         json={"collector_number": "DZ 1234", "type_status": "isotype", "collector_name": "F. Collector",
                               "correction_reason": "Record the collector number from the label"})
    assert updated.status_code == 200, updated.text
    assert client.put("/api/specimen/update-specimen", headers=admin, params={"specimen_id": specimen.specimen_id},
                      json={"type_status": "not-a-type"}).status_code == 422

    draft = {"title": "Voucher set for a taxonomic revision", "license": "CC BY 4.0",
             "description": "Vouchers cited in the article.",
             "contributors": [{"name": "F. Scientist", "role": "curator", "orcid": VALID_ORCID}],
             "specimen_ids": [specimen.specimen_id]}
    bad_orcid = {**draft, "contributors": [{"name": "F. Scientist", "role": "curator", "orcid": "0000-0002-1825-0098"}]}
    assert client.post("/api/depositions", headers=author, json={"institution": "EXU", **bad_orcid}).status_code == 422
    created = client.post("/api/depositions", headers=author, json={"institution": "exu", **draft})
    assert created.status_code == 201, created.text
    path = f"/api/depositions/{created.json()['id']}"
    inputs = client.get(f"{path}/draft/inputs", headers=author).json()
    assert inputs["vouchers"][0]["id"] == specimen.specimen_id and not inputs["vouchers"][0]["is_public"]
    pending = client.get(f"{path}/draft/preview", headers=author)
    assert [item["id"] for item in pending.json()["releases"]["vouchers"]] == [specimen.specimen_id]
    assert client.put(f"/api/specimen/{specimen.specimen_id}/visibility", headers=admin,
                      json={"is_public": True, "public_location": "region"}).status_code == 200

    with monkeypatch.context() as patch:
        patch.setattr(settings, "PUBLIC_BASE_URL", "")
        missing_base = client.get(f"{path}/draft/preview", headers=author)
        assert missing_base.status_code == 409 and "PUBLIC_BASE_URL" in missing_base.text
    preview = client.get(f"{path}/draft/preview", headers=author).json()
    snapshot = preview["snapshot"]
    assert snapshot["profiles"] == []
    assert snapshot["institution_identifiers"] == {"index_herbariorum": None, "ror": "https://ror.org/05pn4ss79"}
    voucher = snapshot["vouchers"][0]
    assert voucher["collector_number"] == "DZ 1234" and voucher["type_status"] == "isotype"
    assert "collector_name" not in voucher
    assert snapshot["contributors"] == draft["contributors"]
    published = client.post(f"{path}/publish", headers=admin, json={
        key: preview[key] for key in ("draft_revision", "snapshot_sha256")})
    assert published.status_code == 200, published.text
    identity = published.json()
    assert identity["url"] == f"{BASE_URL}/api/depositions/public/EXU/{created.json()['accession']}/versions/1"
    assert identity["identifier"] == identity["url"].replace("/api/depositions/public/", "/depositions/")

    page = client.get(identity["identifier"])
    assert page.status_code == 200
    for text in ("Vouchers", "DZ 1234", "Isotype", f"ORCID {VALID_ORCID}", identity["identifier"]):
        assert text in page.text
    bundle = client.get(f"{identity['url']}/archive.zip")
    zip_path = tmp_path / "vouchers.zip"
    zip_path.write_bytes(bundle.content)
    entries = verify_archive(zip_path, identity["snapshot_sha256"])["entries"]
    assert [entry["path"] for entry in entries] == ["deposition.json"]
    with ZipFile(zip_path) as archive:
        assert sorted(archive.namelist()) == ["deposition.json", "manifest.json"]

    datacite = client.get(f"{identity['url']}/datacite.json").json()
    assert datacite["url"] == identity["identifier"]
    assert datacite["creators"][0]["nameIdentifiers"][0]["nameIdentifier"] == f"https://orcid.org/{VALID_ORCID}"
    assert datacite["publisher"]["publisherIdentifier"] == "https://ror.org/05pn4ss79"
    assert datacite["types"]["resourceTypeGeneral"] == "Dataset" and "doi" not in datacite

    calls = []

    class FakeZenodo:
        def _reply(self, payload):
            return SimpleNamespace(status_code=201, text="", content=b"{}", json=lambda: payload)

        def post(self, url, **options):
            calls.append(("POST", url, options))
            if url.endswith("/actions/publish"):
                return self._reply({"doi": "10.5281/zenodo.1234", "links": {"html": "https://zenodo.org/records/1234"}})
            return self._reply({"id": 1234, "links": {"bucket": "https://zenodo.org/api/files/bucket"}})

        def put(self, url, **options):
            calls.append(("PUT", url, options))
            return self._reply({})

    monkeypatch.setattr(settings, "ZENODO_TOKEN", "test-token")
    accession = created.json()["accession"]
    dry_run = mirror("EXU", accession, 1, "curator@example.org", dry_run=True)
    assert dry_run["metadata"]["license"] == "cc-by-4.0" and dry_run["metadata"]["creators"][0]["orcid"] == VALID_ORCID
    registered = mirror("EXU", accession, 1, "curator@example.org", session=FakeZenodo())
    assert registered["doi"] == "10.5281/zenodo.1234"
    uploaded = next(options for method, url, options in calls if url.startswith("https://zenodo.org/api/files/"))
    assert uploaded["data"] == bundle.content
    with pytest.raises(ValueError, match="already has the dataset DOI"):
        mirror("EXU", accession, 1, "curator@example.org", session=FakeZenodo())

    doi_route = f"{path}/versions/1/doi"
    assert client.put(doi_route, headers=author, json={"doi": "10.5281/zenodo.1234", "agency": "zenodo"}).status_code == 403
    assert client.put(doi_route, headers=admin, json={"doi": "10.5281/ZENODO.1234", "agency": "zenodo"}).status_code == 200
    assert client.put(doi_route, headers=admin, json={"doi": "10.5281/zenodo.9999", "agency": "zenodo"}).status_code == 409
    record = client.get(identity["url"]).json()
    assert record["dataset_doi"]["url"] == "https://doi.org/10.5281/zenodo.1234"
    assert record["snapshot_sha256"] == identity["snapshot_sha256"]
    assert client.get(f"{identity['url']}/datacite.json").json()["doi"] == "10.5281/zenodo.1234"
    assert "https://doi.org/10.5281/zenodo.1234" in client.get(identity["identifier"]).text


def test_version_2_archives_must_list_every_voucher(tmp_path):
    source = b"feature,value,confidence\r\nA,100,annotated\r\n"
    profile = {"id": "profile", "voucher": {"id": "voucher"},
               "file": {"size": len(source), "sha256": sha256(source).hexdigest()}}
    snapshot = {"schema_version": 2, "institution": "EXU", "accession": "a", "version": 1,
                "vouchers": [{"id": "voucher"}], "profiles": [profile]}
    path = tmp_path / "v2.zip"
    path.write_bytes(build_archive(snapshot, {"profile": source}))
    assert verify_archive(path, snapshot_digest(snapshot))["entries"][1]["path"] == "files/001.csv"
    for broken, message in (
        ({**snapshot, "vouchers": []}, "between one and 250 vouchers"),
        ({**snapshot, "vouchers": [{"id": "other"}]}, "voucher must be listed"),
        ({**snapshot, "vouchers": [{"id": "voucher"}, {"id": "voucher"}]}, "duplicate voucher"),
    ):
        with pytest.raises(ValueError, match=message):
            manifest_for(broken, b"{}")


def test_zenodo_license_mapping():
    assert zenodo_license("CC BY 4.0") == "cc-by-4.0"
    assert zenodo_license("Creative Commons Attribution 4.0 International") == "cc-by-4.0"
    assert zenodo_license("CC0 1.0") == "cc0-1.0"
    with pytest.raises(ValueError, match="--license"):
        zenodo_license("All rights reserved")


def test_identifier_migration_registers_existing_institutions_and_field_widening_is_reversible():
    scripts = migrations()
    with sa.create_engine("sqlite://").begin() as connection:
        with Operations.context(MigrationContext.configure(connection)):
            for revision in ("0001", "0002", "0003", "0004", "0005", "0006", "0007", "0008"):
                scripts.get_revision(revision).module.upgrade()
            metadata = sa.MetaData()
            tables = {name: sa.Table(name, metadata, autoload_with=connection)
                      for name in ("users", "deposition", "field_loc")}
            connection.execute(tables["users"].insert().values(user_id="owner"))
            connection.execute(tables["deposition"].insert().values(
                id="d1", institution="OLD", accession="a1", owner_id="owner",
                draft={"institution_name": "Old University"}, draft_revision="r1", latest_version=0))
            scripts.get_revision("0009").module.upgrade()
            institutions = sa.Table("institution", sa.MetaData(), autoload_with=connection)
            assert connection.execute(sa.select(institutions.c.code, institutions.c.name)).all() == [
                ("OLD", "Old University")]

            scripts.get_revision("0009").module.downgrade()
            connection.execute(tables["field_loc"].insert().values(
                field_loc_id="f1", country="Serbia", region="Pčinja District",
                locality="Northern slope of Mt Besna Kobila above the village of Gornja Lisina, beech forest"))
            with pytest.raises(RuntimeError, match="truncate field_loc.locality"):
                scripts.get_revision("0008").module.downgrade()
            connection.execute(tables["field_loc"].update().values(locality="Besna Kobila", region="Pčinja"))
            scripts.get_revision("0008").module.downgrade()
            columns = {column["name"] for column in sa.inspect(connection).get_columns("field_loc")}
            assert "coordinate_uncertainty_m" not in columns
