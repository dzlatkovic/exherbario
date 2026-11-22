import pytest

from app import demo
from app.chemistry.models import Profile, SpreadsheetImport, Study
from app.config import settings
from app.deposition.models import Deposition, DepositionVersion
from app.specimen.models import Specimen
from app.tests import TestClass, TestingSessionLocal, client
from app.users.models import User


class TestDemoSeed(TestClass):
    def counts(self):
        with TestingSessionLocal() as db:
            return {model.__name__: db.query(model).count()
                    for model in (User, Specimen, Study, Profile, SpreadsheetImport, Deposition, DepositionVersion)}

    def test_seed_and_reset(self, pubchem, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(demo, "LOOKUPS_PATH", tmp_path / "lookups.json")
        with pytest.raises(demo.DemoError, match="DEMO_MODE"):
            demo.seed(live=False)
        monkeypatch.setattr(settings, "DEMO_MODE", True)
        monkeypatch.setattr(settings, "PUBLIC_BASE_URL", "https://demo.example.org")
        # The recorded PubChem data of the test suite stands in for live PubChem; GBIF is offline in tests.
        monkeypatch.setattr(demo.RecordedLookups, "_live_pubchem", lambda self: pubchem)

        demo.seed(live=True, record=True)
        seeded = self.counts()
        assert seeded == {"User": 2, "Specimen": len(demo.VOUCHERS), "Study": 4, "Profile": 4,
                          "SpreadsheetImport": 3, "Deposition": 3, "DepositionVersion": 2}
        with TestingSessionLocal() as db:
            states = sorted((bool(item.latest_version), item.submitted_at is not None, bool(item.draft))
                            for item in db.query(Deposition))
            assert states == [(False, False, True), (False, True, True), (True, False, False)]
            versions = db.query(DepositionVersion).order_by(DepositionVersion.number).all()
            assert versions[1].snapshot["correction_reason"].startswith("Voucher DEMO-003 redetermined")
            assert {profile.technique for profile in db.query(Profile)} == {"GC-MS", "isolation"}
            # Publishing released what the published deposition contains.
            yarrow = db.query(Study).filter(Study.title.startswith("Essential oils of Achillea")).one()
            assert yarrow.is_public
        assert (tmp_path / "lookups.json").exists()  # what was looked up, for offline seeding

        page = client.get(versions[1].snapshot["identifier"].removeprefix("https://demo.example.org"))
        assert page.status_code == 200 and "demonstration deposition" in page.text
        with pytest.raises(demo.DemoError, match="already has accounts"):
            demo.seed(live=False)

        demo.reset(live=False)  # offline, from the recorded lookups
        assert self.counts() == seeded
