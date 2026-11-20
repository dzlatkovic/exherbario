"""A PubChem stand-in for tests, serving the records in fixtures/pubchem.json."""

import json
from pathlib import Path

from app.chemistry.names import name_key
from app.chemistry.pubchem import PubChemUnavailable

FIXTURES = Path(__file__).with_name("fixtures") / "pubchem.json"


class FakePubChem:
    def __init__(self, path: Path = FIXTURES):
        self.records = json.loads(path.read_text(encoding="utf-8"))["records"]
        self.available = True
        self.calls = []

    def _check(self, call):
        self.calls.append(call)
        if not self.available:
            raise PubChemUnavailable("PubChem stand-in switched off")

    def compounds(self, namespace, identifier):
        self._check((namespace, identifier))
        if namespace == "cid":
            wanted = [int(value) for value in (identifier if isinstance(identifier, list) else [identifier])]
            return [dict(record) for cid in wanted for record in self.records if record["cid"] == cid]
        if namespace == "inchikey":
            return [dict(record) for record in self.records if record["inchikey"] == identifier]
        key = name_key(str(identifier))
        return [dict(record) for record in self.records
                if key in {name_key(name) for name in [record["title"], *record["synonyms"]]}]

    def same_connectivity(self, cid):
        self._check(("same_connectivity", cid))
        block = next(record["inchikey"][:14] for record in self.records if record["cid"] == cid)
        return [record["cid"] for record in self.records if record["inchikey"].startswith(block)]
