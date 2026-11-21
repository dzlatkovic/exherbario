"""Shared test setup: no test reaches PubChem or any other external service."""

import pytest

from app.chemistry.routes import get_pubchem
from app.chemistry.tests.fake_pubchem import FakePubChem
from app.main import app


@pytest.fixture(autouse=True)
def pubchem():
    fake = FakePubChem()
    app.dependency_overrides[get_pubchem] = lambda: fake
    yield fake
    app.dependency_overrides.pop(get_pubchem, None)


@pytest.fixture(autouse=True)
def offline(monkeypatch):
    """Any HTTP request a test has not replaced fails as if the machine were offline."""
    import requests

    def refuse(*_args, **_kwargs):
        raise requests.ConnectionError("Network access is disabled in tests.")
    monkeypatch.setattr(requests.adapters.HTTPAdapter, "send", refuse)
