"""Collector numbers, type status, georeference details and widened text fields."""

import subprocess
import sys
from pathlib import Path

import sqlalchemy as sa

from app.tests import client
from app.tests.test_depositions import headers_for
from app.tests.test_sqlite_deployment import sqlite_archive  # noqa: F401  (pytest fixture)
from app.users.services import UserServices

LOCALITY = "Northern slope of Mt Besna Kobila above the village of Gornja Lisina, beech forest near the spring"


def test_registration_keeps_full_labels_collector_numbers_and_georeferences(sqlite_archive):  # noqa: F811
    admin = headers_for(UserServices.create_super_user("Curator", "Example", "curator@example.org", "password"))
    site = client.post("/api/field-locations/create-new-field-loc", headers=admin, json={
        "country": "Serbia", "region": "Pčinja District", "locality": LOCALITY,
        "habitat": "Fagus sylvatica forest on silicate bedrock, north-facing slope", "altitude": 1650,
        "gps_lat": 42.5341, "gps_long": 22.2183, "coordinate_uncertainty_m": 30,
        "geodetic_datum": "WGS84", "georeference_source": "Handheld GPS",
    })
    assert site.status_code == 200, site.text
    assert site.json()["locality"] == LOCALITY and site.json()["coordinate_uncertainty_m"] == 30
    assert client.post("/api/field-locations/create-new-field-loc", headers=admin, json={
        "country": "Serbia", "region": "Pčinja", "locality": "x", "coordinate_uncertainty_m": -1,
    }).status_code == 422
    corrected = client.put("/api/field-locations/update-field-loc", headers=admin,
                           params={"field_loc_id": site.json()["field_loc_id"]},
                           json={"coordinate_uncertainty_m": 100, "correction_reason": "Re-read the GPS log"})
    assert corrected.status_code == 200, corrected.text

    voucher = client.post("/api/specimen/create-new-specimen", headers=admin, json={
        "holding_type": "local", "holding_institution": "Example University", "collection": "Herbarium",
        "accession": "BOT-2026-000042", "collector_name": "D. Zlatković", "collector_number": "DZ 1234",
        "verbatim_collection_date": "mid-June 2026", "type_status": "holotype",
        "field_loc_id": site.json()["field_loc_id"], "reg_no": "LEGACY-2026-000042",
    })
    assert voucher.status_code == 200, voucher.text
    specimen_id = voucher.json()["specimen_id"]
    label = client.get("/api/specimen/get-herbarium-label", headers=admin, params={"specimen_id": specimen_id}).json()
    assert label["collector_number"] == "DZ 1234" and label["type_status"] == "holotype"
    assert label["verbatim_collection_date"] == "mid-June 2026" and label["coordinate_uncertainty_m"] == 100

    assert client.put(f"/api/specimen/{specimen_id}/visibility", headers=admin,
                      json={"is_public": True, "public_location": "region"}).status_code == 200
    public = client.get(f"/api/specimen/{specimen_id}").json()
    assert public["collector_number"] == "DZ 1234" and public["type_status"] == "holotype"
    assert public["location"] == {"region": "Pčinja District", "country": "Serbia"}
    assert LOCALITY not in client.get(f"/api/specimen/{specimen_id}").text


def test_migrations_round_trip_on_sqlite(tmp_path, monkeypatch):
    database = tmp_path / "round-trip.db"
    url = sa.URL.create("sqlite", database=str(database))
    monkeypatch.setenv("DATABASE_URL", url.render_as_string(hide_password=False))
    project = Path(__file__).resolve().parents[2]
    for command in (["upgrade", "head"], ["downgrade", "0007"], ["upgrade", "head"]):
        subprocess.run([sys.executable, "-m", "alembic", *command], cwd=project, check=True, timeout=60)
    engine = sa.create_engine(url)
    with engine.connect() as connection:
        columns = {column["name"]: column for column in sa.inspect(connection).get_columns("field_loc")}
        assert columns["locality"]["type"].length == 500 and "geodetic_datum" in columns
        assert connection.exec_driver_sql("PRAGMA foreign_key_check").all() == []
    engine.dispose()
