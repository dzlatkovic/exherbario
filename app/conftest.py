"""Shared test setup: no test reaches the real PubChem."""

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
