"""The local compound registry, author aliases and compound matching, backed by PubChem."""

from urllib.parse import quote

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import ChemistryStructure, Compound, CompoundAlias, CompoundName
from app.chemistry.names import INCHIKEY, cas_numbers, name_key, stereo_unspecified, valid_cas
from app.chemistry.pubchem import PubChemClient, PubChemUnavailable, structure_image_url
from app.chemistry.sample_links import utc_now
from app.chemistry.structures import StructureError, parse_structure

UNAVAILABLE = "PubChem could not be reached. Try again later, or enter a CID that is already registered."


def compound_summary(compound: Compound) -> dict:
    return {
        "cid": compound.cid, "title": compound.title, "iupac_name": compound.iupac_name,
        "molecular_formula": compound.molecular_formula, "monoisotopic_mass": compound.monoisotopic_mass,
        "inchi": compound.inchi, "inchikey": compound.inchikey, "smiles": compound.smiles,
        "cas_numbers": compound.cas_numbers, "cas_source": "PubChem synonyms",
        "structure_image": structure_image_url(compound.cid), "retrieved_at": compound.retrieved_at,
    }


def record_of(compound: Compound) -> dict:
    return {"cid": compound.cid, "title": compound.title, "iupac_name": compound.iupac_name,
            "molecular_formula": compound.molecular_formula, "monoisotopic_mass": compound.monoisotopic_mass,
            "inchi": compound.inchi, "inchikey": compound.inchikey, "smiles": compound.smiles,
            "synonyms": compound.synonyms}


def depiction_url(smiles: str) -> str:
    return "/api/chemistry/depict.svg?smiles=" + quote(smiles, safe="")


def structure_summary(structure: ChemistryStructure) -> dict:
    return {"id": structure.id, "name": structure.name, "molecular_formula": structure.molecular_formula,
            "monoisotopic_mass": structure.monoisotopic_mass, "inchi": structure.inchi,
            "inchikey": structure.inchikey, "smiles": structure.smiles, "source": "author-supplied",
            "submitted_at": structure.submitted_at}


def structure_record(structure: dict, existing: ChemistryStructure | None = None) -> dict:
    """A review candidate for a structure the author supplied and PubChem does not have."""
    return {"cid": None, "structure_id": existing.id if existing else None,
            "title": existing.name if existing else "Structure supplied by the author", "iupac_name": None,
            **{key: structure[key] for key in ("molecular_formula", "monoisotopic_mass", "inchi", "inchikey", "smiles")},
            "synonyms": []}


def candidate_summary(record: dict) -> dict:
    """What the review shows for a candidate."""
    summary = {key: record[key] for key in ("cid", "title", "molecular_formula", "monoisotopic_mass", "inchikey",
                                            "smiles")}
    if record["cid"] is None:
        return summary | {"author_structure": True, "structure_image": depiction_url(record["smiles"])}
    return summary | {"structure_image": structure_image_url(record["cid"])}


class CompoundRegistry:
    def __init__(self, db: Session, pubchem: PubChemClient | None = None):
        self.db = db
        self.pubchem = pubchem or PubChemClient()

    def _remote(self, namespace, identifier):
        try:
            return self.pubchem.compounds(namespace, identifier)
        except PubChemUnavailable as error:
            raise ChemistryError(503, UNAVAILABLE) from error

    def _store(self, record: dict) -> Compound:
        compound = self.db.get(Compound, record["cid"])
        if compound is None:
            compound = Compound(cid=record["cid"])
            self.db.add(compound)
        for field in ("title", "iupac_name", "molecular_formula", "monoisotopic_mass", "inchi", "inchikey",
                      "smiles", "synonyms"):
            setattr(compound, field, record[field])
        compound.cas_numbers = cas_numbers(record["synonyms"])
        compound.retrieved_at = utc_now()
        self.db.execute(delete(CompoundName).where(CompoundName.cid == compound.cid))
        keys = {name_key(compound.title): True}
        for synonym in record["synonyms"]:
            keys.setdefault(name_key(synonym), False)
        self.db.add_all(CompoundName(cid=compound.cid, name_key=key, is_title=is_title)
                        for key, is_title in keys.items() if key)
        self.db.flush()
        return compound

    def register(self, record: dict) -> Compound:
        """Store a PubChem record the author confirmed."""
        return self._store(record)

    def register_structure(self, record: dict, name: str, owner_id: str) -> ChemistryStructure:
        """Store an author-supplied structure the author confirmed; the same structure is stored once."""
        structure = self.db.scalar(select(ChemistryStructure).where(ChemistryStructure.inchikey == record["inchikey"]))
        if structure is None:
            computed = parse_structure(record["smiles"])
            if computed["inchikey"] != record["inchikey"]:
                raise ChemistryError(409, "The structure changed during review. Look it up again.")
            structure = ChemistryStructure(
                name=name[:500], submitted_by=owner_id, submitted_at=utc_now(),
                **{key: computed[key] for key in ("inchikey", "inchi", "smiles", "molecular_formula",
                                                  "monoisotopic_mass")})
            self.db.add(structure)
            self.db.flush()
        return structure

    def _lookup(self, namespace: str, identifier) -> dict | None:
        """A record from the registry, else from PubChem, without storing it."""
        if namespace == "cid":
            compound = self.db.get(Compound, identifier)
        else:
            compound = self.db.scalar(select(Compound).where(Compound.inchikey == identifier).order_by(Compound.cid))
        if compound is not None:
            return record_of(compound)
        records = self._remote(namespace, identifier)
        return records[0] if records else None

    def _cas_lookup(self, cas: str) -> dict | None:
        local = [compound for compound in self.db.scalars(
            select(Compound).join(CompoundName).where(CompoundName.name_key == name_key(cas)))
            if cas in compound.cas_numbers]
        if local:
            return record_of(local[0])
        records = [record for record in self._remote("name", cas) if cas in cas_numbers(record["synonyms"])]
        return records[0] if records else None

    def get(self, cid: int) -> Compound:
        """The registered compound, fetched from PubChem and stored on first use."""
        compound = self.db.get(Compound, cid)
        if compound is not None:
            return compound
        record = self._lookup("cid", cid)
        if record is None:
            raise ChemistryError(404, f"PubChem has no compound with CID {cid}.")
        return self._store(record)

    def _structure_lookup(self, smiles: str) -> dict:
        """The registered or PubChem compound with the structure's InChIKey, else the author's structure itself."""
        try:
            structure = parse_structure(smiles)
        except StructureError as error:
            raise ChemistryError(422, str(error)) from error
        if self.db.scalar(select(Compound.cid).where(Compound.inchikey == structure["inchikey"]).limit(1)) is None:
            existing = self.db.scalar(select(ChemistryStructure).where(
                ChemistryStructure.inchikey == structure["inchikey"]))
            if existing is not None:
                return structure_record(structure, existing)
        return self._lookup("inchikey", structure["inchikey"]) or structure_record(structure)

    def lookup_identifiers(self, cid=None, inchikey=None, cas=None, smiles=None) -> tuple[dict, str] | None:
        """Resolve identifiers given in a file. When several are given they must name the same compound.

        With a SMILES (or molfile) the InChIKey is computed from it; a structure PubChem does not have is
        returned as an author-supplied record (``cid`` None), which is stored only when the author confirms it."""
        found = []
        for namespace, value, lookup in (("cid", cid, lambda: self._lookup("cid", cid)),
                                         ("smiles", smiles, lambda: self._structure_lookup(smiles)),
                                         ("inchikey", None if smiles else inchikey,
                                          lambda: self._lookup("inchikey", inchikey)),
                                         ("cas", cas, lambda: self._cas_lookup(cas))):
            if value is None or value == "":
                continue
            record = lookup()
            if record is None:
                raise ChemistryError(404, f"PubChem has no compound for {namespace} {value}.")
            found.append((record, "author_structure" if record["cid"] is None else namespace))
        if len({record["cid"] for record, _ in found}) > 1:
            raise ChemistryError(422, "The CID, InChIKey and CAS given for one row name different compounds.")
        return found[0] if found else None

    def local_name_matches(self, name: str) -> list[tuple[Compound, str]]:
        rows = self.db.execute(
            select(Compound, CompoundName.is_title).join(CompoundName)
            .where(CompoundName.name_key == name_key(name))
            .order_by(CompoundName.is_title.desc(), Compound.cid)
        ).all()
        return [(compound, "registry_name" if is_title else "registry_synonym") for compound, is_title in rows]

    def alias(self, owner_id: str, name: str) -> Compound | None:
        alias = self.db.get(CompoundAlias, (owner_id, name_key(name)[:160]))
        return self.db.get(Compound, alias.cid) if alias else None

    def save_alias(self, owner_id: str, name: str, cid: int):
        key = name_key(name)[:160]
        alias = self.db.get(CompoundAlias, (owner_id, key))
        if alias is None:
            alias = CompoundAlias(owner_id=owner_id, name_key=key)
            self.db.add(alias)
        alias.name, alias.cid, alias.updated_at = name[:160], cid, utc_now()

    def match_name(self, owner_id: str, name: str) -> dict:
        """Propose a compound for a name: the author's alias, then the registry, then PubChem.

        Candidates are records; nothing is stored until the author confirms a choice."""
        compound = self.alias(owner_id, name)
        if compound is not None:
            return {"proposal": record_of(compound), "method": "alias", "status": "confirmed",
                    "candidates": [record_of(compound)]}
        local = self.local_name_matches(name)
        if local:
            candidates = [record_of(compound) for compound, _ in local]
            # One registered compound whose preferred name is exactly this name: accepted, still changeable in review.
            exact = local[0][1] == "registry_name" and sum(method == "registry_name" for _, method in local) == 1
            return {"proposal": candidates[0], "method": local[0][1], "candidates": candidates,
                    "status": "confirmed" if exact else "needs_review"}
        try:
            records = self.pubchem.compounds("name", name)
        except PubChemUnavailable:
            return {"proposal": None, "method": None, "status": "unmatched", "candidates": [],
                    "problem": "PubChem could not be reached."}
        if not records:
            return {"proposal": None, "method": None, "status": "unmatched", "candidates": []}
        if name_key(records[0]["title"]) == name_key(name):
            # PubChem's preferred name is exactly the name in the table: accepted, still changeable in review.
            return {"proposal": records[0], "method": "pubchem_title", "status": "confirmed", "candidates": records}
        return {"proposal": records[0], "method": "pubchem_name", "status": "needs_review", "candidates": records}

    def search(self, query: str, namespace: str) -> list[dict]:
        """Candidate records for a manual search by name, CAS, CID or InChIKey: the registry first, then PubChem."""
        query = query.strip()
        if namespace == "cid":
            if not query.isdigit() or not 0 < int(query) < 2 ** 31:
                raise ChemistryError(422, "Enter a positive whole-number CID.")
            record = self._lookup("cid", int(query))
        elif namespace == "inchikey":
            if not INCHIKEY.match(query):
                raise ChemistryError(422, "Enter a full InChIKey, e.g. GRWFGVWFFZKLTI-UHFFFAOYSA-N.")
            record = self._lookup("inchikey", query)
        elif namespace == "cas":
            if not valid_cas(query):
                raise ChemistryError(422, "Enter a CAS number with a valid check digit, e.g. 80-56-8.")
            record = self._cas_lookup(query)
        elif namespace == "name" and query:
            found = {compound.cid: record_of(compound) for compound, _ in self.local_name_matches(query)}
            for record in self._remote("name", query):
                found.setdefault(record["cid"], record)
            return list(found.values())
        else:
            raise ChemistryError(422, "Search by name, cas, cid or inchikey.")
        return [record] if record else []

    def parent(self, cid: int, record: dict | None = None) -> dict:
        """The stereo-unspecified record with the same connectivity, e.g. α-pinene for (+)-α-pinene."""
        record = record or self._lookup("cid", cid)
        if record is None:
            raise ChemistryError(404, f"PubChem has no compound with CID {cid}.")
        if stereo_unspecified(record["inchikey"]):
            return record
        try:
            related = sorted(set(self.pubchem.same_connectivity(cid)) - {cid})[:20]
        except PubChemUnavailable as error:
            raise ChemistryError(503, UNAVAILABLE) from error
        for candidate in (self._remote("cid", related) if related else []):
            if stereo_unspecified(candidate["inchikey"]):
                return candidate
        raise ChemistryError(404, "PubChem lists no stereo-unspecified parent for this compound.")
