"""PubChem access through PubChemPy. Everything else in HERBAR uses the local compound registry."""

import socket
from urllib.error import URLError

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


class PubChemClient:
    """Live PubChem client. Tests replace it with a client that serves recorded responses."""

    def __init__(self, timeout: float = 15):
        self.timeout = timeout

    def _call(self, function, *args, **kwargs):
        previous = socket.getdefaulttimeout()
        socket.setdefaulttimeout(self.timeout)
        try:
            return function(*args, **kwargs)
        except pubchempy.NotFoundError:
            return []
        except (pubchempy.PubChemPyError, URLError, OSError) as error:
            raise PubChemUnavailable(str(error)) from error
        finally:
            socket.setdefaulttimeout(previous)

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
        return [int(value) for value in self._call(
            pubchempy.get_cids, cid, "cid", searchtype="fastidentity", identity_type="same_connectivity")]
