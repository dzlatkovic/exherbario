"""Validate uploaded analytical tables and identification evidence before storing any rows."""

import csv
import math
from io import StringIO

from app.chemistry.names import INCHIKEY, valid_cas

MAX_CSV_BYTES = 512 * 1024
MAX_FEATURES = 1000
STATUSES = {"measured", "not_detected", "not_measured"}
GC_TECHNIQUES = {"GC-MS", "GC-FID"}
LC_MS_TECHNIQUES = {"LC-MS", "LC-MS/MS"}
POLARITY_CLASSES = ("non-polar", "semi-polar", "polar")
RI_TOLERANCE = 20
ID_BASIS = {"ri": "RI", "ms": "MS", "ms library": "MS", "library": "MS", "standard": "standard",
            "reference standard": "standard", "std": "standard", "ms/ms": "MS/MS", "msms": "MS/MS",
            "literature": "literature", "lit": "literature"}
ID_BASIS_ORDER = ("RI", "MS", "standard", "MS/MS", "literature")
QUALIFIERS = {"trace": "trace", "tr": "trace", "<loq": "<LOQ", "loq": "<LOQ"}
IDENTIFIERS = ("cid", "inchikey", "cas")
COMMON = ("rt_min", "id_basis", "id_level", "qualifier", "sd", "n")
GC_ONLY = ("ri_exp", "ri_ref", "ri_ref_source", "ri_ref_polarity")
GC_MS_ONLY = ("library_match", "library_score")
LC_MS_ONLY = ("mz_obs", "adduct", "mass_error_ppm", "msms_match")
EVIDENCE = (*COMMON, *GC_ONLY, *GC_MS_ONLY, *LC_MS_ONLY)
TEXT_LIMITS = {"ri_ref_source": 200, "library_match": 200, "adduct": 40, "msms_match": 200}
CSV_COLUMNS = ("feature", "value", "confidence", "status", *IDENTIFIERS, *EVIDENCE)


def allowed_columns(technique: str | None) -> set[str]:
    allowed = set(COMMON) | set(IDENTIFIERS)
    if technique in GC_TECHNIQUES:
        allowed |= set(GC_ONLY)
    if technique == "GC-MS":
        allowed |= set(GC_MS_ONLY)
    if technique in LC_MS_TECHNIQUES:
        allowed |= set(LC_MS_ONLY)
    return allowed


def _number(text, label, where, *, integer=False, minimum=None):
    try:
        value = float(text.replace(",", ".")) if not integer else int(text)
    except ValueError as error:
        raise ValueError(f"{where}: {label} must be a {'whole ' if integer else ''}number.") from error
    if not math.isfinite(value) or (minimum is not None and value < minimum):
        raise ValueError(f"{where}: {label} is out of range.")
    return value


def parse_evidence(raw: dict, where: str, technique: str | None, run_metadata: dict | None,
                   ri_tolerance: float = RI_TOLERANCE) -> tuple[dict, dict, list[str]]:
    """Validate a row's identifiers and evidence. Returns (identifiers, evidence fields, warnings)."""
    raw = {key: (value or "").strip() for key, value in raw.items() if (value or "").strip()}
    extra = set(raw) - allowed_columns(technique)
    if extra:
        raise ValueError(f"{where}: {', '.join(sorted(extra))} cannot be recorded for {technique or 'this profile'}.")
    identifiers = {}
    if "cid" in raw:
        identifiers["cid"] = int(_number(raw["cid"], "CID", where, integer=True, minimum=1))
    if "inchikey" in raw:
        if not INCHIKEY.match(raw["inchikey"]):
            raise ValueError(f"{where}: the InChIKey is not in the standard 27-character form.")
        identifiers["inchikey"] = raw["inchikey"]
    if "cas" in raw:
        if not valid_cas(raw["cas"]):
            raise ValueError(f"{where}: the CAS number has an invalid format or check digit.")
        identifiers["cas"] = raw["cas"]

    fields, warnings = {}, []
    for name in ("rt_min", "sd", "ri_exp", "ri_ref", "library_score", "mz_obs"):
        if name in raw:
            fields[name] = _number(raw[name], name, where, minimum=0)
    if "mass_error_ppm" in raw:
        fields["mass_error_ppm"] = _number(raw["mass_error_ppm"], "mass_error_ppm", where)
    if "n" in raw:
        fields["n"] = int(_number(raw["n"], "n", where, integer=True, minimum=1))
    for name, limit in TEXT_LIMITS.items():
        if name in raw:
            if len(raw[name]) > limit:
                raise ValueError(f"{where}: {name} is longer than {limit} characters.")
            fields[name] = raw[name]
    if "qualifier" in raw:
        qualifier = QUALIFIERS.get(raw["qualifier"].casefold())
        if not qualifier:
            raise ValueError(f"{where}: qualifier must be trace or <LOQ.")
        fields["qualifier"] = qualifier
    basis = set()
    if "id_basis" in raw:
        for token in raw["id_basis"].replace(",", ";").split(";"):
            if token.strip():
                if token.strip().casefold() not in ID_BASIS:
                    raise ValueError(f"{where}: unknown identification basis {token.strip()!r}. "
                                     "Use RI, MS, standard, MS/MS or literature.")
                basis.add(ID_BASIS[token.strip().casefold()])
        fields["id_basis"] = ";".join(item for item in ID_BASIS_ORDER if item in basis)
    if "id_level" in raw:
        level = int(_number(raw["id_level"], "id_level", where, integer=True, minimum=1))
        if level > 4:
            raise ValueError(f"{where}: id_level must be an MSI level from 1 to 4.")
        if level == 1 and "standard" not in basis:
            raise ValueError(f"{where}: MSI level 1 requires identification against a reference standard.")
        fields["id_level"] = level
    if "RI" in basis and "ri_exp" not in fields:
        raise ValueError(f"{where}: give the experimental RI (ri_exp) when the identification uses RI.")
    if "ri_ref_polarity" in raw:
        polarity = raw["ri_ref_polarity"].casefold()
        if polarity not in POLARITY_CLASSES:
            raise ValueError(f"{where}: ri_ref_polarity must be non-polar, semi-polar or polar.")
        run_polarity = (run_metadata or {}).get("polarity_class")
        if run_polarity and polarity != run_polarity:
            raise ValueError(f"{where}: the reference RI is for a {polarity} column, but the run used a "
                             f"{run_polarity} column.")
        fields["ri_ref_polarity"] = polarity
    if "ri_exp" in fields and "ri_ref" in fields and abs(fields["ri_exp"] - fields["ri_ref"]) > ri_tolerance:
        warnings.append(f"{where}: experimental RI {fields['ri_exp']:g} differs from the reference "
                        f"{fields['ri_ref']:g} by more than {ri_tolerance:g}.")
    return identifiers, fields, warnings


def check_values(rows: list[dict], basis: str):
    if not any(row["value"] is not None for row in rows):
        raise ValueError("Include at least one measured feature.")
    if basis == "peak_area_percent" and sum(row["value"] or 0 for row in rows) > 100.5:
        raise ValueError("Peak-area percentages must total at most 100%, allowing minor rounding.")


def read_measurements(content: bytes, basis: str, technique: str | None = None, run_metadata: dict | None = None):
    """Parse a per-profile CSV. Returns (decoded source, rows, warnings); identifiers stay in each row."""
    if len(content) > MAX_CSV_BYTES:
        raise ValueError("The CSV exceeds the 512 KiB limit.")
    try:
        source = content.decode("utf-8-sig")
    except UnicodeDecodeError as error:
        raise ValueError("Save the CSV as UTF-8 and try again.") from error
    reader = csv.DictReader(StringIO(source, newline=""), strict=True)
    required = {"feature", "value", "confidence"}
    rows, warnings = [], []
    try:
        headers = reader.fieldnames or []
        if len(headers) != len(set(headers)) or not required.issubset(headers) or set(headers) - set(CSV_COLUMNS):
            raise ValueError("Use the CSV columns feature,value,confidence with optional status, identifier "
                             "and evidence columns (see the documentation).")
        seen = set()
        for row in reader:
            line = reader.line_num
            where = f"Row {line}"
            if len(rows) >= MAX_FEATURES:
                raise ValueError(f"A profile supports at most {MAX_FEATURES} features.")
            if None in row or any(value is None for value in row.values()):
                raise ValueError(f"Row {line} has the wrong number of columns.")
            feature = row["feature"].strip()
            confidence = row["confidence"].strip()
            status = row.get("status", "").strip() or "measured"
            if not feature or len(feature) > 160 or feature.casefold() in seen:
                raise ValueError(f"Row {line} needs a unique feature name of up to 160 characters.")
            if not confidence or len(confidence) > 30 or status not in STATUSES:
                raise ValueError(f"Row {line} has an invalid confidence label or measurement status.")
            identifiers, evidence, row_warnings = parse_evidence(
                {key: row[key] for key in row if key in IDENTIFIERS or key in EVIDENCE}, where, technique, run_metadata)
            warnings += row_warnings
            raw_value = row["value"].strip()
            if status != "measured":
                if raw_value or evidence.get("qualifier"):
                    raise ValueError(f"Leave the value and qualifier blank for an unmeasured feature on row {line}.")
                value = None
            elif not raw_value and evidence.get("qualifier"):
                value = None
            else:
                try:
                    value = float(raw_value)
                except ValueError as error:
                    raise ValueError(f"Row {line} needs a numeric value or a trace / <LOQ qualifier.") from error
                if not math.isfinite(value) or value < 0 or (basis == "peak_area_percent" and value > 100):
                    raise ValueError(f"Row {line} has a value outside the allowed range.")
            seen.add(feature.casefold())
            rows.append({"feature": feature, "confidence": confidence, "status": status, "value": value,
                         "identifiers": identifiers, **evidence})
    except csv.Error as error:
        raise ValueError(f"Malformed CSV near row {reader.line_num}.") from error
    check_values(rows, basis)
    return source, rows, warnings
