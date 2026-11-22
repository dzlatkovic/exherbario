"""Synthetic demonstration data for a DEMO_MODE instance.

    python -m app.demo seed              # fill an empty demo database
    python -m app.demo seed --if-empty   # the same, and do nothing if it already has accounts (for start-up)
    python -m app.demo reset             # wipe every record and upload, then seed again
    python -m app.demo record            # look everything up live once and save it, so seeding works offline

Everything here is invented: vouchers carry DEMO- accessions and the chemistry is made up, although real
species and real compound names are used so that the demo looks like real work. All commands refuse to run
unless DEMO_MODE is on, so a real instance cannot be wiped by mistake.

Records are created through the HTTP API in-process, as a researcher and a curator would create them, so the
demo exercises the same checks as real use and stays valid after upgrades. PubChem and GBIF answers come from
app/demo_data/lookups.json when it is there, and live otherwise.
"""

import argparse
import asyncio
import copy
import json
import logging
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from app.config import settings
from app.demo_accounts import DEMO_ACCOUNTS

LOOKUPS_PATH = Path(__file__).resolve().parent / "demo_data" / "lookups.json"
INSTITUTION = {"code": "DEMO", "name": "Demo University Herbarium"}
PLANTAE_GBIF_KEY = "6"
logger = logging.getLogger(__name__)


class DemoError(RuntimeError):
    pass


# The synthetic dataset ---------------------------------------------------------------------------------------

TAXA = {
    "Achillea millefolium": "L.",
    "Achillea collina": "(Becker ex Rchb.f.) Heimerl",
    "Artemisia absinthium": "L.",
    "Hypericum perforatum": "L.",
    "Salvia officinalis": "L.",
    "Thymus serpyllum": "L.",
    "Juniperus communis": "L.",
}

# accession, taxon, collector number, collection date, region, locality, altitude, habitat, lat, lon,
# released, public locality
VOUCHERS = [
    ("DEMO-001", "Achillea millefolium", "AD-101", "2025-06-12", "Nišava", "Suva planina, below Trem", 1350,
     "Dry grassland", 43.18, 22.17, True, "region"),
    ("DEMO-002", "Achillea millefolium", "AD-102", "2025-06-14", "Zlatibor", "Tornik, upper slopes", 1420,
     "Mountain meadow", 43.67, 19.67, True, "region"),
    ("DEMO-003", "Achillea millefolium", "AD-103", "2025-06-20", "Pirot", "Stara planina, Babin zub", 1600,
     "Subalpine pasture", 43.37, 22.62, True, "region"),
    ("DEMO-004", "Achillea millefolium", "AD-104", "2025-07-02", "Zlatibor", "Mokra Gora, road verge", 700,
     "Roadside", 43.79, 19.51, True, "withheld"),
    ("DEMO-005", "Achillea millefolium", "AD-105", "2025-07-03", "Nišava", "Sićevo gorge", 300,
     "Limestone rocks", 43.33, 22.08, False, "withheld"),
    ("DEMO-006", "Artemisia absinthium", "AD-201", "2025-08-05", "Šumadija", "Rudnik, abandoned field", 650,
     "Ruderal", 44.13, 20.51, True, "region"),
    ("DEMO-007", "Artemisia absinthium", "AD-202", "2025-08-06", "Šumadija", "Rudnik, village edge", 600,
     "Ruderal", 44.14, 20.50, True, "region"),
    ("DEMO-008", "Hypericum perforatum", "AD-301", "2025-07-10", "Zaječar", "Rtanj, northern slopes", 900,
     "Forest clearing", 43.78, 21.89, True, "region"),
    ("DEMO-009", "Hypericum perforatum", "AD-302", "2025-07-11", "Zaječar", "Rtanj, Šiljak path", 1200,
     "Grassland", 43.77, 21.90, False, "withheld"),
    ("DEMO-010", "Salvia officinalis", "AD-401", "2025-06-01", "Belgrade", "Botanical garden, cultivated", 120,
     "Cultivated", 44.81, 20.48, True, "region"),
    ("DEMO-011", "Salvia officinalis", "AD-402", "2025-06-01", "Belgrade", "Botanical garden, cultivated", 120,
     "Cultivated", 44.81, 20.48, True, "region"),
    ("DEMO-012", "Salvia officinalis", "AD-403", "2025-06-02", "Srem", "Fruška gora, private garden", 250,
     "Cultivated", 45.15, 19.80, True, "region"),
    ("DEMO-013", "Thymus serpyllum", "AD-501", "2025-07-15", "Pirot", "Stara planina, Midžor ridge", 2000,
     "Alpine grassland", 43.39, 22.68, True, "region"),
    ("DEMO-014", "Thymus serpyllum", "AD-502", "2025-07-16", "Pirot", "Stara planina, Kopren", 1900,
     "Alpine grassland", 43.36, 22.64, False, "withheld"),
    ("DEMO-015", "Juniperus communis", "AD-601", "2025-09-03", "Zlatibor", "Čigota", 1400,
     "Shrubland", 43.70, 19.75, True, "region"),
    ("DEMO-016", "Juniperus communis", "AD-602", "2025-09-04", "Zlatibor", "Murtenica", 1300,
     "Shrubland", 43.60, 19.88, True, "region"),
]

GC_RUN = {"column": "HP-5MS (30 m × 0.25 mm, 0.25 µm)", "polarity_class": "non-polar",
          "stationary_phase": "5% phenyl methylpolysiloxane",
          "temperature_programme": "60 °C to 246 °C at 3 °C/min", "carrier_gas": "He, 1 mL/min",
          "alkane_series": "C8–C20", "ri_type": "linear_temperature_programmed"}
# Compound, RI exp, RI lit, identification, % in the three populations (synthetic)
YARROW_OIL = [
    ("α-Pinene", 932, 932, "RI; MS; co-injection", 4.2, 6.8, 2.1),
    ("Sabinene", 969, 969, "RI; MS", 8.4, 3.1, 11.6),
    ("β-Pinene", 974, 974, "RI; MS; co-injection", 6.1, 7.5, 3.0),
    ("Myrcene", 988, 988, "RI; MS", 1.2, 0.9, "tr"),
    ("p-Cymene", 1020, 1020, "RI; MS", 2.3, "tr", 1.4),
    ("Limonene", 1024, 1024, "RI; MS", 1.0, 1.8, "nd"),
    ("1,8-Cineole", 1026, 1026, "RI; MS; co-injection", 18.5, 9.7, 22.4),
    ("γ-Terpinene", 1054, 1054, "RI; MS", 0.8, 1.6, 0.4),
    ("Camphor", 1141, 1141, "RI; MS", 9.6, 14.2, 5.3),
    ("Borneol", 1165, 1165, "RI; MS", 3.4, 4.9, 2.2),
    ("Terpinen-4-ol", 1174, 1174, "RI; MS", 2.7, 1.1, 3.9),
    ("β-Caryophyllene", 1417, 1417, "RI; MS", 5.5, 6.3, 4.1),
    ("Germacrene D", 1484, 1480, "RI; MS", 7.9, 10.4, 6.6),
    ("Caryophyllene oxide", 1582, 1582, "RI; MS", 3.1, 2.4, 4.8),
    ("Unidentified sesquiterpene alcohol", 1641, None, "MS", 1.9, "nd", 2.6),
]
SAGE_OIL = [
    ("α-Thujone", 1101, 1101, "RI; MS", 24.1, 31.5),
    ("β-Thujone", 1112, 1112, "RI; MS", 6.2, 4.8),
    ("Camphor", 1141, 1141, "RI; MS", 15.3, 11.0),
    ("1,8-Cineole", 1026, 1026, "RI; MS", 12.7, 9.9),
    ("Viridiflorol", 1592, 1592, "RI; MS", 4.4, 7.2),
]
ISOLATION_RUN = {"isolation_procedure": "CH2Cl2 extract (5.2 g): silica gel CC, n-hexane–EtOAc gradient (F1–F12); "
                                        "F7: Sephadex LH-20 (MeOH); semi-preparative HPLC, C18, MeOH–H2O 65:35",
                 "nmr_spectrometer": "Bruker Avance III HD", "nmr_frequency_mhz": 600,
                 "nmr_solvent": "CDCl3", "hrms_instrument": "Orbitrap", "hrms_ionisation": "ESI±"}
NEW_LACTONE = "C=C1C(=O)O[C@@H]2[C@H]1CC[C@@H](C)[C@@H]1CC[C@](C)(O)[C@H]12"
# Compound, SMILES, mg, NMR experiments, solvent, new/known, DOI, optical rotation, CCDC, configuration type,
# configuration, identification, level, observed m/z, adduct
ISOLATED = [
    ("Absinthiolide A", NEW_LACTONE, 12.4, "1H, 13C, DEPT, COSY, HSQC, HMBC, NOESY", "CDCl3", "new", None,
     "[α]D20 −42.0 (c 0.10, CHCl3)", "CCDC 1234567", "absolute", "Relative by NOESY; absolute by X-ray",
     "NMR; HRMS; X-ray", 1, 273.1458, "[M+Na]+"),
    ("Scopoletin", "COc1cc2ccc(=O)oc2cc1O", 8.1, "1H, 13C, HMBC", "CD3OD", "known", "10.1000/demo.scopoletin",
     None, None, None, None, "NMR; HRMS; literature", 2, 193.0497, "[M+H]+"),
    ("Apigenin", "O=c1cc(-c2ccc(O)cc2)oc2cc(O)cc(O)c12", 5.6, "1H, 13C", "DMSO-d6", "known",
     "10.1000/demo.apigenin", None, None, None, None, "NMR; HRMS; literature", 2, 269.0451, "[M-H]-"),
    ("β-Sitosterol", None, 21.0, "1H, 13C", "CDCl3", "known", "10.1000/demo.sitosterol", None, None, None, None,
     "NMR; literature", 2, None, None),
    ("Compound 6", None, 0.9, "1H", "CDCl3", None, None, None, None, None, None, "NMR", 3, None, None),
]


# Lookups that work offline once recorded --------------------------------------------------------------------

class RecordedLookups:
    """PubChem and GBIF answers, from app/demo_data/lookups.json when recorded, else live (and then kept)."""

    def __init__(self, live: bool):
        self.live = live
        self.answers = json.loads(LOOKUPS_PATH.read_text(encoding="utf-8")) if LOOKUPS_PATH.exists() else {}
        self.recorded = {}
        self._pubchem = None

    def _answer(self, key, fetch):
        if key in self.answers:
            self.recorded[key] = self.answers[key]
            return copy.deepcopy(self.answers[key])
        if not self.live:
            from app.chemistry.pubchem import PubChemUnavailable
            raise PubChemUnavailable(f"No recorded answer for {key}.")
        answer = fetch()
        self.answers[key] = self.recorded[key] = answer
        return copy.deepcopy(answer)

    def pubchem(self):
        lookups = self

        class Client:
            def compounds(self, namespace, identifier):
                return lookups._answer(f"pubchem:{namespace}:{json.dumps(identifier, ensure_ascii=False)}",
                                       lambda: lookups._live_pubchem().compounds(namespace, identifier))

            def same_connectivity(self, cid):
                return lookups._answer(f"pubchem:same_connectivity:{cid}",
                                       lambda: lookups._live_pubchem().same_connectivity(cid))

        return Client()

    def _live_pubchem(self):
        if self._pubchem is None:
            from app.chemistry.pubchem import PubChemClient
            self._pubchem = PubChemClient()
        return self._pubchem

    def gbif_key(self, name):
        def fetch():
            import requests
            answer = requests.get("https://api.gbif.org/v1/species/match", params={"name": name, "strict": "true"},
                                  timeout=15).json()
            return str(answer["usageKey"]) if answer.get("usageKey") else None
        try:
            key = self._answer(f"gbif:{name}", fetch)
        except Exception:  # noqa: BLE001 - offline: a demo key, without a GBIF link that works
            key = None
        return key or f"demo-{abs(hash(name)) % 10 ** 8}"

    def save(self):
        LOOKUPS_PATH.parent.mkdir(parents=True, exist_ok=True)
        LOOKUPS_PATH.write_text(json.dumps(dict(sorted(self.recorded.items())), indent=1, ensure_ascii=False) + "\n",
                                encoding="utf-8")


# Building the demo through the API --------------------------------------------------------------------------

class Demo:
    def __init__(self, lookups: RecordedLookups):
        from fastapi.testclient import TestClient

        from app.chemistry.routes import get_pubchem
        from app.main import app

        self.lookups = lookups
        app.dependency_overrides[get_pubchem] = lookups.pubchem
        # Not used as a context manager, so the app's start-up (and the nightly reset) does not run again.
        self.client = TestClient(app, base_url=settings.PUBLIC_BASE_URL or "http://demo.invalid")
        self.app = app
        self.voucher_ids = {}

    def close(self):
        from app.chemistry.routes import get_pubchem
        self.app.dependency_overrides.pop(get_pubchem, None)

    def call(self, method, path, who, expected=(200, 201, 204), **kwargs):
        response = self.client.request(method, path, headers=self.headers[who], **kwargs)
        if response.status_code not in expected:
            raise DemoError(f"{method} {path} answered {response.status_code}: {response.text[:500]}")
        return response.json() if response.content and response.headers.get("content-type", "").startswith(
            "application/json") else None

    # People, taxa, vouchers ------------------------------------------------------------------------------

    def people(self):
        from app.users.services import UserServices, signJWT

        curator, researcher = DEMO_ACCOUNTS
        users = {"curator": UserServices.create_super_user(curator["name"], curator["surname"], curator["email"],
                                                           settings.DEMO_PASSWORD),
                 "researcher": UserServices.create_user(researcher["name"], researcher["surname"],
                                                        researcher["email"], settings.DEMO_PASSWORD)}
        self.users = users
        self.headers = {who: {"Authorization": "Bearer " + signJWT(
            user.user_id, "super_user" if user.is_superuser else "classic_user")["access_token"]}
            for who, user in users.items()}

    def taxa(self):
        from app.db import SessionLocal
        from app.taxonomy.repository import TaxonomyRepository
        from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank

        self.taxon_ids = {}
        with SessionLocal() as db:
            repository = TaxonomyRepository(db)
            plantae = repository.create_taxon(TaxonomySchemaIn(taxon_name="Plantae", gbif_key=PLANTAE_GBIF_KEY),
                                              TaxonRank.KINGDOM)
            for name, authority in TAXA.items():
                taxon = repository.create_taxon(TaxonomySchemaIn(
                    taxon_name=name, gbif_key=self.lookups.gbif_key(name), authority=authority,
                    parent_taxon_key=plantae.taxon_id), TaxonRank.SPECIES)
                self.taxon_ids[name] = taxon.taxon_id

    def vouchers(self):
        self.call("POST", "/api/institutions", "curator", json=INSTITUTION)
        for (accession, taxon, number, collected, region, locality, altitude, habitat, lat, lon, released,
             location) in VOUCHERS:
            created = self.call("POST", "/api/specimen/create-new-specimen", "curator", json={
                "holding_type": "local", "holding_institution": INSTITUTION["name"], "collection": "Demo vouchers",
                "accession": accession, "collector_name": "A. Demo", "collector_number": number,
                "collection_date": collected, "taxon_id": self.taxon_ids[taxon],
                "subnomen": f"{taxon} {TAXA[taxon]}", "determiner_name": "B. Demo",
                "determination_date": collected,
                "verbatim_label": f"Synthetic demonstration label. {locality}, {altitude} m, {habitat}.",
                "field_location": {"country": "Serbia", "region": region, "locality": locality,
                                   "altitude": altitude, "habitat": habitat, "gps_lat": lat, "gps_long": lon}})
            self.voucher_ids[accession] = created["specimen_id"]
            if released:
                self.release_voucher(accession, location)

    def release_voucher(self, accession, location="region"):
        self.call("PUT", f"/api/specimen/{self.voucher_ids[accession]}/visibility", "curator",
                  json={"is_public": True, "public_location": location})

    # Studies -----------------------------------------------------------------------------------------------

    def study(self, title, description):
        return self.call("POST", "/api/chemistry/studies", "researcher",
                         json={"title": title, "description": description})["id"]

    def sample(self, study, code, voucher, preparation, **sample):
        created = self.call("POST", f"/api/chemistry/studies/{study}/sample-preparations", "researcher", json={
            "sample": {"code": code, "vouchers": [{"specimen_id": self.voucher_ids[voucher],
                                                   "role": "sampled_from_voucher"}],
                       "site_specimen_id": self.voucher_ids[voucher], **sample},
            "preparation": preparation})
        return created["preparation"]["id"]

    def upload(self, study, name, rows):
        from openpyxl import Workbook

        book = Workbook()
        book.active.title = "Table 1"
        for row in rows:
            book.active.append(list(row))
        output = BytesIO()
        book.save(output)
        return self.call("POST", f"/api/chemistry/studies/{study}/imports", "researcher",
                         files={"file": (name, output.getvalue(), "application/octet-stream")})["id"]

    def import_table(self, study, name, rows, roles, preparations, settings_):
        """Upload, assign, look up, review (accept every proposal; no match → unidentified) and confirm."""
        draft = self.upload(study, name, rows)
        url = f"/api/chemistry/imports/{draft}"
        columns = []
        for index, role in enumerate(roles):
            column = {"index": index, "role": role}
            if role == "sample":
                column["preparation_id"] = preparations.pop(0)
            columns.append(column)
        self.call("PUT", f"{url}/assignment", "researcher", json={
            "sheet": "Table 1", "header_row": 1, "columns": columns, "settings": settings_})
        for _ in range(20):
            matched = self.call("POST", f"{url}/match", "researcher")
            if not matched["pending"] or matched["problem"]:
                break
        for row in matched["review"]:
            if row["status"] == "confirmed":
                continue
            action = "accept" if row["match"] else "unidentified"
            self.call("PUT", f"{url}/rows/{row['row']}/compound", "researcher", json={"action": action})
        return [profile["id"] for profile in self.call("POST", f"{url}/confirm", "researcher")["profiles"]]

    def presets(self):
        self.call("PUT", "/api/chemistry/condition-presets", "researcher", json={
            "kind": "run", "name": "HP-5MS, essential oils", "values": {
                "technique": "GC-MS", "measurement_basis": "peak_area_percent", "unit": "%", "run_metadata": GC_RUN}})
        self.call("PUT", "/api/chemistry/condition-presets", "researcher", json={
            "kind": "preparation", "name": "Hydrodistillation, Clevenger, 3 h", "values": {
                "kind": "essential_oil", "method_reference": "Hydrodistillation (European Pharmacopoeia 2.8.12)",
                "method_parameters": "Clevenger-type apparatus, 3 h"}})

    def yarrow(self):
        study = self.study("Essential oils of Achillea millefolium from three populations (demo)",
                           "Synthetic demonstration study: GC-MS composition of hydrodistilled oils from three "
                           "populations in Serbia, each sample linked to its voucher.")
        oil = {"kind": "essential_oil", "method_reference": "Hydrodistillation (European Pharmacopoeia 2.8.12)",
               "method_parameters": "Clevenger-type apparatus, 3 h", "plant_material_mass_g": 100}
        preparations = [self.sample(study, code, voucher, {**oil, "yield_percent": oil_yield},
                                    plant_part="aerial parts", material_state="air-dried", collection_date=date,
                                    phenological_stage="full flowering", drying_notes="Air-dried in shade, 10 days")
                        for code, voucher, oil_yield, date in (("AM-1", "DEMO-001", 0.42, "2025-06-12"),
                                                                ("AM-2", "DEMO-002", 0.31, "2025-06-14"),
                                                                ("AM-3", "DEMO-003", 0.55, "2025-06-20"))]
        rows = [("Compound", "RI exp", "RI lit", "Identification", "AM-1", "AM-2", "AM-3"),
                *[(name, ri, ri_lit, basis, *values) for name, ri, ri_lit, basis, *values in YARROW_OIL]]
        return self.import_table(study, "yarrow-oils.xlsx", rows,
                                 ["name", "ri_exp", "ri_ref", "id_basis", "sample", "sample", "sample"], preparations,
                                 {"technique": "GC-MS", "measurement_basis": "peak_area_percent", "unit": "%",
                                  "run_metadata": GC_RUN})

    def wormwood(self):
        from app.chemistry.structures import expected_mz, mass_error_ppm, parse_structure

        study = self.study("Compounds isolated from Artemisia absinthium aerial parts (demo)",
                           "Synthetic demonstration study: isolated compounds with structure-determination "
                           "conditions; Absinthiolide A is an invented new compound.")
        extract = self.sample(study, "AA-1", "DEMO-006", {
            "kind": "extract", "method_reference": "Maceration in CH2Cl2, 3 × 24 h, room temperature",
            "plant_material_mass_g": 250}, plant_part="aerial parts", material_state="air-dried",
            collection_date="2025-08-05")
        rows = [("Compound", "SMILES", "AA-1", "NMR experiments", "Solvent", "New or known", "Literature DOI",
                 "Optical rotation", "CCDC", "Configuration type", "Configuration", "Identification", "Level",
                 "m/z", "Adduct", "Δ ppm")]
        for name, smiles, mg, nmr, solvent, novelty, doi, rotation, ccdc, kind, configuration, basis, level, mz, \
                adduct in ISOLATED:
            ppm = None
            if smiles and mz:
                ppm = round(mass_error_ppm(mz, expected_mz(parse_structure(smiles)["monoisotopic_mass"], adduct)), 1)
            rows.append((name, smiles, mg, nmr, solvent, novelty, doi, rotation, ccdc, kind, configuration, basis,
                         level, mz, adduct, ppm))
        roles = ["name", "smiles", "sample", "nmr_experiments", "nmr_solvent", "novelty", "literature_doi",
                 "optical_rotation", "ccdc", "configuration_type", "configuration", "id_basis", "id_level",
                 "mz_obs", "adduct", "mass_error_ppm"]
        return self.import_table(study, "wormwood-isolated.xlsx", rows, roles, [extract], {
            "technique": "isolation", "measurement_basis": "isolated_mass", "unit": "mg",
            "run_metadata": ISOLATION_RUN})

    def st_johns_wort(self):
        study = self.study("Antimicrobial screening of a Hypericum perforatum extract (demo)",
                           "Synthetic demonstration study: an extract tested in a bioassay and deposited without "
                           "chemical analysis.")
        return self.sample(study, "HP-1", "DEMO-008", {
            "kind": "extract", "method_reference": "Ultrasound-assisted extraction in methanol, 3 × 30 min",
            "method_parameters": "Solvent evaporated under reduced pressure at 40 °C",
            "plant_material_mass_g": 20, "yield_percent": 18.5}, plant_part="flower", material_state="air-dried",
            collection_date="2025-07-10", phenological_stage="full flowering")

    def sage(self):
        """A study left for visitors: an uploaded table whose columns are not assigned and whose samples do not
        exist yet, to try the column assignment, the bulk dialog and the PubChem review."""
        study = self.study("Essential oils of cultivated Salvia officinalis (demo, try the import here)",
                           "Synthetic demonstration study for visitors: open the unfinished import, create the "
                           "samples from the vouchers DEMO-010 and DEMO-011, and review the compounds.")
        rows = [("No.", "Compound", "RI exp", "RI lit", "Identification", "SO-1", "SO-2"),
                *[(index, *item) for index, item in enumerate(SAGE_OIL, 1)]]
        self.upload(study, "sage-oils.xlsx", rows)

    # Depositions --------------------------------------------------------------------------------------------

    def deposition(self, title, description, **selection):
        return self.call("POST", "/api/depositions", "researcher", json={
            "institution": INSTITUTION["code"], "title": title, "description": description, "license": "CC BY 4.0",
            "contributors": [{"name": "Demo Researcher", "role": "analyst"},
                             {"name": "Demo Curator", "role": "curator"}], **selection})

    def publish(self, deposition_id):
        preview = self.call("GET", f"/api/depositions/{deposition_id}/draft/preview", "curator")
        self.call("POST", f"/api/depositions/{deposition_id}/publish", "curator", json={
            key: preview[key] for key in ("draft_revision", "snapshot_sha256", "releases_sha256") if preview.get(key)})

    def depositions(self, yarrow_runs, isolation_runs, extract):
        published = self.deposition(
            "Dataset for: Essential oils of Achillea millefolium from three populations (demo)",
            "Synthetic demonstration dataset: three GC-MS profiles of essential oils, each linked to its voucher.",
            profile_ids=yarrow_runs)
        self.publish(published["id"])
        # The DEMO-003 voucher is redetermined after publication, and a correction (version 2) records it.
        self.call("PUT", "/api/specimen/update-specimen", "curator",
                  params={"specimen_id": self.voucher_ids["DEMO-003"]},
                  json={"taxon_id": self.taxon_ids["Achillea collina"],
                        "subnomen": f"Achillea collina {TAXA['Achillea collina']}", "determiner_name": "C. Demo",
                        "determination_date": "2025-11-02"})
        draft = self.call("GET", f"/api/depositions/{published['id']}/draft", "researcher")
        start = draft["published"]["correction_start"]
        self.call("PUT", f"/api/depositions/{published['id']}/draft", "researcher", json={
            **start, "expected_revision": None,
            "correction_reason": "Voucher DEMO-003 redetermined as Achillea collina."})
        self.publish(published["id"])

        submitted = self.deposition(
            "Dataset for: Compounds isolated from Artemisia absinthium (demo)",
            "Synthetic demonstration dataset: isolated compounds with structure-determination conditions.",
            profile_ids=isolation_runs)
        self.call("POST", f"/api/depositions/{submitted['id']}/submission", "researcher")

        self.deposition("Antimicrobial Hypericum perforatum extract (demo)",
                        "Synthetic demonstration draft: an extract deposited without analytical runs.",
                        preparation_ids=[extract])

    def build(self):
        self.people()
        self.taxa()
        self.vouchers()
        self.presets()
        yarrow_runs = self.yarrow()
        isolation_runs = self.wormwood()
        extract = self.st_johns_wort()
        self.sage()
        self.depositions(yarrow_runs, isolation_runs, extract)


# Commands ---------------------------------------------------------------------------------------------------

def _require_demo():
    if not settings.DEMO_MODE:
        raise DemoError("DEMO_MODE is off. The demo commands only run on a demonstration instance.")
    if not settings.PUBLIC_BASE_URL.strip():
        raise DemoError("Set PUBLIC_BASE_URL (the demo's address) before seeding: the demo publishes depositions.")


def _has_accounts() -> bool:
    from sqlalchemy import func, select

    from app.db import SessionLocal
    from app.users.models import User

    with SessionLocal() as db:
        return bool(db.scalar(select(func.count()).select_from(User)))


def seed(live: bool = True, record: bool = False):
    _require_demo()
    if _has_accounts():
        raise DemoError("The database already has accounts. Use reset to start the demo again.")
    lookups = RecordedLookups(live)
    demo = Demo(lookups)
    try:
        demo.build()
    finally:
        demo.close()
    if record:
        lookups.save()


def wipe():
    """Delete every record (the schema stays) and every stored upload and photograph."""
    _require_demo()
    import app.main  # noqa: F401 - registers every model
    from app.db import Base, SessionLocal
    from app.file_storage import FILES_ROOT
    from app.image.services.image_services import IMAGE_ROOT

    with SessionLocal() as db:
        for table in reversed(Base.metadata.sorted_tables):
            db.execute(table.delete())
        db.commit()
    for root in (FILES_ROOT, IMAGE_ROOT):
        if root.is_dir():
            for path in root.iterdir():
                if path.is_file():
                    path.unlink()


def reset(live: bool = True):
    wipe()
    seed(live)


def seconds_until(hour: int, now: datetime | None = None) -> float:
    now = now or datetime.now(timezone.utc)
    target = now.replace(hour=hour, minute=0, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return (target - now).total_seconds()


async def nightly_reset(hour: int):
    """Started by the app on a demo instance: reset the demo every day at the given UTC hour."""
    while True:
        await asyncio.sleep(seconds_until(hour))
        try:
            await asyncio.to_thread(reset)
            logger.info("The demo was reset.")
        except Exception:  # noqa: BLE001 - keep the schedule running; the next night tries again
            logger.exception("The nightly demo reset failed.")


def record():
    """Seed a throwaway demo database with live PubChem and GBIF, and save their answers for offline use."""
    with tempfile.TemporaryDirectory() as folder:
        environment = {**os.environ, "DATA_DIR": folder, "DATABASE_URL": f"sqlite:///{Path(folder) / 'demo.db'}",
                       "DEMO_MODE": "true", "PUBLIC_BASE_URL": settings.PUBLIC_BASE_URL or "https://demo.invalid"}
        subprocess.run([sys.executable, "-m", "alembic", "upgrade", "head"], check=True, env=environment)
        subprocess.run([sys.executable, "-m", "app.demo", "seed", "--record-lookups"], check=True, env=environment)
    print(f"Saved the lookups to {LOOKUPS_PATH}. Commit it so the demo seeds without network access.")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("command", choices=("seed", "reset", "record"))
    parser.add_argument("--if-empty", action="store_true", help="seed only a database without accounts")
    parser.add_argument("--offline", action="store_true", help="use only the recorded lookups")
    parser.add_argument("--record-lookups", action="store_true", help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        if args.command == "record":
            record()
        elif args.command == "reset":
            reset(live=not args.offline)
        elif args.if_empty and (not settings.DEMO_MODE or _has_accounts()):
            print("Nothing to seed: " + ("DEMO_MODE is off." if not settings.DEMO_MODE else "the demo has accounts."))
        else:
            seed(live=not args.offline, record=args.record_lookups)
    except DemoError as error:
        raise SystemExit(str(error)) from None


if __name__ == "__main__":
    main()
