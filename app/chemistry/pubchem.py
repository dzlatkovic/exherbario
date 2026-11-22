"""PubChem access through PubChemPy. Everything else in HERBAR uses the local compound registry."""

import json
import threading
import time
from urllib.error import URLError
from urllib.request import urlopen as _urlopen

import pubchempy

PROPERTIES = ["Title", "IUPACName", "MolecularFormula", "MonoisotopicMass", "InChI", "InChIKey", "SMILES"]
MAX_CANDIDATES = 10
MAX_SYNONYMS = 50
NAMESPACES = ("name", "cid", "inchikey")


class PubChemUnavailable(Exception):
    """PubChem could not be reached or answered with an error."""


def structure_image_url(cid: int) -> str:
    return f"https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound/cid/{cid}/PNG"


def _record(row: dict, synonyms: list[str]) -> dict:
    smiles = row.get("SMILES") or row.get("IsomericSMILES") or row.get("CanonicalSMILES")
    mass = row.get("MonoisotopicMass")
    return {
        "cid": int(row["CID"]), "title": row.get("Title") or f"CID {row['CID']}",
        "iupac_name": row.get("IUPACName"), "molecular_formula": row.get("MolecularFormula"),
        "monoisotopic_mass": float(mass) if mass is not None else None, "inchi": row.get("InChI"),
        "inchikey": row.get("InChIKey"), "smiles": smiles, "synonyms": synonyms[:MAX_SYNONYMS],
    }


DEFAULT_TIMEOUT = 15
_request_timeout = threading.local()


def _urlopen_with_timeout(url, data=None, **kwargs):
    """PubChemPy calls urlopen without a timeout; give each call the timeout of the client making it, without
    changing Python's process-wide socket default (which other threads and libraries rely on)."""
    kwargs.setdefault("timeout", getattr(_request_timeout, "seconds", DEFAULT_TIMEOUT))
    return _urlopen(url, data, **kwargs)


# PubChemPy looks urlopen up in its own module at each request.
pubchempy.urlopen = lambda url, data=None, **kwargs: _urlopen_with_timeout(url, data, **kwargs)


class PubChemClient:
    """Live PubChem client. Tests replace it with a client that serves recorded responses."""

    def __init__(self, timeout: float = DEFAULT_TIMEOUT):
        self.timeout = timeout

    def _call(self, function, *args, **kwargs):
        previous = getattr(_request_timeout, "seconds", None)
        _request_timeout.seconds = self.timeout  # this thread only
        try:
            return function(*args, **kwargs)
        except pubchempy.NotFoundError:
            return []
        except (pubchempy.PubChemPyError, URLError, OSError) as error:
            raise PubChemUnavailable(str(error)) from error
        finally:
            if previous is None:
                del _request_timeout.seconds
            else:
                _request_timeout.seconds = previous

    def compounds(self, namespace: str, identifier) -> list[dict]:
        """Records for up to ten matching compounds, best match first, with synonyms."""
        if namespace not in NAMESPACES:
            raise ValueError(f"Unsupported PubChem namespace: {namespace}")
        rows = self._call(pubchempy.get_properties, PROPERTIES, identifier, namespace)[:MAX_CANDIDATES]
        if not rows:
            return []
        synonyms = {int(row["CID"]): row.get("Synonym", []) for row in self._call(
            pubchempy.get_synonyms, [int(row["CID"]) for row in rows], "cid")}
        return [_record(row, synonyms.get(int(row["CID"]), [])) for row in rows]

    def same_connectivity(self, cid: int) -> list[int]:
        """CIDs that share the compound's connectivity, including its stereoisomers and the unspecified parent."""
        return [int(value) for value in self._call(_same_connectivity_cids, cid)]


def _same_connectivity_cids(cid: int, polls: int = 10) -> list:
    """PubChemPy 1.0.5's get_cids drops the "cids" operation for a fastidentity search, so PubChem answers with
    full compound records and get_cids returns None. Ask for the CID list directly, and follow a ListKey if
    PubChem answers asynchronously."""
    def fetch(identifier, namespace, searchtype=None, **kwargs):
        return json.loads(pubchempy.request(identifier, namespace, "compound", "cids", "JSON", searchtype,
                                            **kwargs).read().decode())

    answer = fetch(cid, "cid", "fastidentity", identity_type="same_connectivity")
    for _ in range(polls):
        if "Waiting" not in answer:
            break
        time.sleep(2)
        answer = fetch(answer["Waiting"]["ListKey"], "listkey")
    else:
        if "Waiting" in answer:
            raise pubchempy.PubChemPyError("PubChem did not finish the same-connectivity search.")
    return (answer.get("IdentifierList") or {}).get("CID") or []
