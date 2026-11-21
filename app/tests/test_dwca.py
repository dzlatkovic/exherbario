"""The Darwin Core Archive: released vouchers only, public-catalog privacy rules, valid meta.xml and EML."""

import csv
import io
import zipfile
from io import BytesIO
from xml.etree import ElementTree

from PIL import Image

from app.chemistry.tests.integration_tests import test_compounds
from app.chemistry.tests.integration_tests.test_sample_vouchers import release_voucher
from app.config import settings
from app.deposition.models import DepositionVersion
from app.publication.models import Publication
from app.specimen.models import Specimen, SpecimenPublication
from app.tests import TestClass, TestingSessionLocal, client
from app.tests import test_record_pages

BASE_URL = "https://herbarium.example.edu"
DWC = "{http://rs.tdwg.org/dwc/text/}"


def read(archive: bytes):
    bundle = zipfile.ZipFile(io.BytesIO(archive))
    tables = {}
    for name in bundle.namelist():
        if name.endswith(".txt"):
            tables[name] = list(csv.DictReader(io.StringIO(bundle.read(name).decode()), delimiter="\t",
                                               quoting=csv.QUOTE_NONE))
    return bundle, tables


class TestDarwinCoreArchive(TestClass):
    setup_profile = test_compounds.TestCompounds.setup_profile
    released_profile = test_record_pages.TestRecordPages.released_profile

    def test_archive_of_released_records(self, monkeypatch):
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE_URL)
        monkeypatch.setattr(settings, "DWC_DATASET_TITLE", "Example University Herbarium")
        monkeypatch.setattr(settings, "DWC_PUBLISHER", "Example University")
        monkeypatch.setattr(settings, "DWC_CONTACT_EMAIL", "herbarium@example.edu")
        owner, curator, voucher, study, profile_id = self.released_profile()
        withheld = client.post("/api/specimen/create-new-specimen", headers=curator, json={
            "holding_type": "external", "holding_institution": "Example University", "collection": "Herbarium",
            "accession": "EU-77", "collector_name": "F. Collector", "collector_number": "FC 9",
            "verbatim_collection_date": "May 1972", "type_status": "isotype", "subnomen": "Achillea sp."}).json()
        release_voucher(curator, withheld["specimen_id"], location="withheld")
        hidden = client.post("/api/specimen/create-new-specimen", headers=curator,
                             json={"holding_type": "local", "accession": "PRIVATE-1"}).json()

        jpeg = BytesIO()
        Image.new("RGB", (4, 4), "green").save(jpeg, "JPEG")
        photos = [client.post("/api/image/upload-image", headers=curator,
                              params={"specimen_id": voucher, "image_type": "herbarium"},
                              files={"file": (f"{index}.jpg", jpeg.getvalue(), "image/jpeg")}).json()["image_id"]
                  for index in range(2)]
        assert client.put(f"/api/image/{photos[0]}/visibility", headers=curator, json={"is_public": True}).status_code == 200
        with TestingSessionLocal() as db:
            publication = Publication("10.3390/plants13010001", "2024", "Plants", "Yarrow oil", "Abstract")
            db.add(publication)
            db.flush()
            db.add(SpecimenPublication(voucher, publication.pub_id))
            db.commit()
            snapshots_before = [(row.deposition_id, row.number, row.snapshot_sha256) for row in db.query(DepositionVersion)]

        response = client.get("/api/dwca.zip")
        assert response.status_code == 200, response.text
        assert response.headers["content-type"] == "application/zip"
        bundle, tables = read(response.content)
        assert sorted(bundle.namelist()) == ["eml.xml", "measurementorfact.txt", "meta.xml", "occurrence.txt"]

        occurrences = {row["catalogNumber"]: row for row in tables["occurrence.txt"]}
        assert "PRIVATE-1" not in occurrences and len(occurrences) == 2
        with TestingSessionLocal() as db:
            first = db.get(Specimen, voucher)
            first_catalog = first.accession or first.reg_no
        regional = occurrences[first_catalog]
        assert regional["occurrenceID"] == f"{BASE_URL}/specimens/{voucher}"
        assert regional["basisOfRecord"] == "PreservedSpecimen"
        assert regional["country"] and regional["stateProvince"]
        assert regional["associatedReferences"] == "https://doi.org/10.3390/plants13010001"
        assert regional["associatedMedia"] == f"{BASE_URL}/api/image/{photos[0]}/content"  # the unapproved photo is left out
        assert regional["license"] == "http://creativecommons.org/licenses/by/4.0/legalcode"

        private = occurrences["EU-77"]
        assert (private["country"], private["stateProvince"]) == ("", "")
        assert private["informationWithheld"] == "Location withheld."
        assert (private["institutionCode"], private["collectionCode"], private["recordNumber"]) == (
            "Example University", "Herbarium", "FC 9")
        assert (private["verbatimEventDate"], private["typeStatus"], private["scientificName"]) == (
            "May 1972", "isotype", "Achillea sp.")
        text = response.content.decode("latin-1")
        assert "F. Collector" not in bundle.read("occurrence.txt").decode() and "F. Collector" not in text

        measurements = tables["measurementorfact.txt"]
        assert measurements and {row["coreid"] for row in measurements} == {regional["occurrenceID"]}
        pinene = next(row for row in measurements if "alpha-Pinene" in row["measurementType"])
        assert pinene["measurementType"] == "peak area percent of alpha-Pinene" and pinene["measurementUnit"] == "%"
        assert pinene["measurementID"] == f"{BASE_URL}/profiles/{profile_id}#α-Pinene"
        assert "PubChem CID 6654" in pinene["measurementRemarks"] and "voucher role: sampled from voucher" in pinene["measurementRemarks"]
        assert any(row["measurementValue"] == "trace" for row in measurements)

        meta = ElementTree.fromstring(bundle.read("meta.xml"))
        core = meta.find(f"{DWC}core")
        assert core.get("rowType") == "http://rs.tdwg.org/dwc/terms/Occurrence"
        assert len(core.findall(f"{DWC}field")) == len(tables["occurrence.txt"][0])
        terms = [field.get("term").rsplit("/", 1)[1] for field in core.findall(f"{DWC}field")]
        assert terms == list(tables["occurrence.txt"][0])
        extension = meta.find(f"{DWC}extension")
        assert extension.get("rowType") == "http://rs.tdwg.org/dwc/terms/MeasurementOrFact"
        assert len(extension.findall(f"{DWC}field")) + 1 == len(measurements[0])

        eml = ElementTree.fromstring(bundle.read("eml.xml"))
        assert eml.findtext("dataset/title") == "Example University Herbarium"
        assert eml.find("dataset/intellectualRights/para/ulink").get("url").endswith("/by/4.0/legalcode")
        assert eml.findtext("dataset/contact/electronicMailAddress") == "herbarium@example.edu"
        assert "2 records" in eml.findtext("dataset/abstract/para")

        only = read(client.get("/api/dwca.zip", params={"holding_institution": "Example University",
                                                       "measurements": False}).content)
        assert [row["catalogNumber"] for row in only[1]["occurrence.txt"]] == ["EU-77"]
        assert "measurementorfact.txt" not in only[0].namelist()
        assert ElementTree.fromstring(only[0].read("meta.xml")).find(f"{DWC}extension") is None

        with TestingSessionLocal() as db:
            assert [(row.deposition_id, row.number, row.snapshot_sha256) for row in db.query(DepositionVersion)] == snapshots_before
        assert hidden["specimen_id"] not in response.content.decode("utf-8", "replace")

    def test_needs_a_public_address_and_a_gbif_licence(self, monkeypatch):
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "")
        missing = client.get("/api/dwca.zip")
        assert missing.status_code == 409 and "PUBLIC_BASE_URL" in missing.json()["detail"]
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", BASE_URL)
        monkeypatch.setattr(settings, "DWC_LICENSE", "All rights reserved")
        assert client.get("/api/dwca.zip").status_code == 409
        monkeypatch.setattr(settings, "DWC_LICENSE", "CC0-1.0")
        empty = read(client.get("/api/dwca.zip").content)
        assert empty[1]["occurrence.txt"] == [] and "measurementorfact.txt" not in empty[0].namelist()
