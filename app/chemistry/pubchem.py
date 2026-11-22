"""PubChem access through PubChemPy. Everything else in HERBAR uses the local compound registry."""

import json
import threading
import time
from urllib.error import HTTPError, URLError
from urllib.request import urlopen as _urlopen

import pubchempy

from app.chemistry.names import pubchem_query

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


# PubChem allows at most 5 requests per second (and 400 per minute) from one address and answers 503 "server
# busy" beyond that. Requests from every thread share one pace, slowed down when PubChem's X-Throttling-Control
# header reports load, and a busy answer is retried after a pause.
MIN_INTERVAL = 0.25
RETRY_PAUSES = (1, 2, 4)
_pace = threading.Lock()
_pace_state = {"next": 0.0, "factor": 1.0}


def _wait_for_turn():
    with _pace:
        now = time.monotonic()
        start = max(now, _pace_state["next"])
        _pace_state["next"] = start + MIN_INTERVAL * _pace_state["factor"]
    if start > now:
        time.sleep(start - now)


def _note_load(headers):
    """Status words in X-Throttling-Control: Green, Yellow, Red, Black (blocked)."""
    status = (headers.get("X-Throttling-Control") or "") if headers is not None else ""
    factor = 8.0 if "Black" in status else 4.0 if "Red" in status else 2.0 if "Yellow" in status else 1.0
    with _pace:
        _pace_state["factor"] = factor


def _urlopen_with_timeout(url, data=None, **kwargs):
    """PubChemPy calls urlopen without a timeout; give each call the timeout of the client making it, without
    changing Python's process-wide socket default (which other threads and libraries rely on), and keep to
    PubChem's request rate."""
    kwargs.setdefault("timeout", getattr(_request_timeout, "seconds", DEFAULT_TIMEOUT))
    for attempt in range(len(RETRY_PAUSES) + 1):
        _wait_for_turn()
        try:
            response = _urlopen(url, data, **kwargs)
        except HTTPError as error:
            _note_load(error.headers)
            if error.code in (429, 503) and attempt < len(RETRY_PAUSES):
                time.sleep(RETRY_PAUSES[attempt])
                continue
            raise
        _note_load(getattr(response, "headers", None))
        return response


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
        if namespace == "name":
            identifier = pubchem_query(identifier)  # PubChem does not recognise Greek letters
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
