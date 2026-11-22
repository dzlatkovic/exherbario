"""Validate uploaded analytical tables and identification evidence before storing any rows."""

import csv
import math
import re
from io import StringIO

from app.chemistry.names import INCHIKEY, valid_cas
from app.chemistry.structures import HRMS_TOLERANCE_PPM, StructureError, expected_mz, mass_error_ppm, parse_structure

MAX_CSV_BYTES = 512 * 1024
MAX_FEATURES = 1000
STATUSES = {"measured", "not_detected", "not_measured"}
GC_TECHNIQUES = {"GC-MS", "GC-FID"}
LC_MS_TECHNIQUES = {"LC-MS", "LC-MS/MS"}
POLARITY_CLASSES = ("non-polar", "semi-polar", "polar")
RI_TOLERANCE = 20
ISOLATION = "isolation"
ID_BASIS = {"ri": "RI", "ms": "MS", "ms library": "MS", "library": "MS", "standard": "standard",
            "reference standard": "standard", "std": "standard", "co-injection": "co-injection",
            "coinjection": "co-injection", "co-inj": "co-injection", "coinj": "co-injection",
            "co-injection with standard": "co-injection", "ms/ms": "MS/MS", "msms": "MS/MS",
            "hrms": "HRMS", "hr-ms": "HRMS", "nmr": "NMR", "x-ray": "X-ray", "xray": "X-ray", "scxrd": "X-ray",
            "x-ray crystallography": "X-ray", "ecd": "ECD", "literature": "literature", "lit": "literature"}
ID_BASIS_ORDER = ("RI", "MS", "standard", "co-injection", "MS/MS", "HRMS", "NMR", "X-ray", "ECD", "literature")
# MSI level 1 needs comparison with an authentic sample; for an isolated compound, full structure elucidation.
LEVEL_ONE = {"standard", "co-injection"}
LEVEL_ONE_ISOLATION = LEVEL_ONE | {"NMR", "X-ray"}
AUTHENTIC = {"standard", "co-injection"}
QUALIFIERS = {"trace": "trace", "tr": "trace", "<loq": "<LOQ", "loq": "<LOQ"}
STANDARD_SOURCES = {"commercial": "commercial", "purchased": "commercial", "synthesized": "synthesized",
                    "synthesised": "synthesized", "synthetic": "synthesized", "synthesis": "synthesized",
                    "isolated": "isolated", "isolated in study": "isolated", "gift": "gift", "donated": "gift"}
NOVELTY = {"new": "new", "novel": "new", "new compound": "new", "known": "known", "known compound": "known",
           "previously reported": "known"}
CONFIGURATION_TYPES = {"absolute": "absolute", "relative": "relative", "not determined": "not_determined",
                       "not_determined": "not_determined", "undetermined": "not_determined", "none": "not_determined",
                       "unknown": "not_determined"}
NMR_EXPERIMENTS = {
    "1h": "1H", "h1": "1H", "proton": "1H", "13c": "13C", "c13": "13C", "carbon": "13C", "dept": "DEPT",
    "dept135": "DEPT", "dept90": "DEPT", "dept45": "DEPT", "apt": "APT", "cosy": "COSY", "dqfcosy": "COSY",
    "tocsy": "TOCSY", "hsqc": "HSQC", "edhsqc": "HSQC", "hsqced": "HSQC", "hmqc": "HMQC", "hmbc": "HMBC",
    "h2bc": "H2BC", "noesy": "NOESY", "1dnoesy": "NOESY", "noe": "NOE", "noediff": "NOE", "roesy": "ROESY",
    "adequate": "ADEQUATE", "11adequate": "ADEQUATE", "inadequate": "INADEQUATE", "jres": "J-resolved",
    "jresolved": "J-resolved", "dosy": "DOSY", "15n": "15N", "15nhmbc": "15N", "19f": "19F", "31p": "31P",
}
NMR_ORDER = ("1H", "13C", "DEPT", "APT", "COSY", "TOCSY", "HSQC", "HMQC", "HMBC", "H2BC", "NOESY", "NOE", "ROESY",
             "ADEQUATE", "INADEQUATE", "J-resolved", "DOSY", "15N", "19F", "31P")
SUPERSCRIPTS = str.maketrans("¹²³⁴⁵⁶⁷⁸⁹⁰", "1234567890")
DOI = re.compile(r"^(?:https?://(?:dx\.)?doi\.org/|doi:\s*)?(10\.\d{4,9}/\S+)$", re.IGNORECASE)
CCDC = re.compile(r"^(?:CCDC\s*(?:no\.?\s*)?)?(\d{5,8})$", re.IGNORECASE)
IDENTIFIERS = ("cid", "inchikey", "cas", "smiles")
COMMON = ("rt_min", "id_basis", "id_level", "qualifier", "sd", "n", "standard_source", "standard_reference",
          "data_accessions")
GC_ONLY = ("ri_exp", "ri_ref", "ri_ref_source", "ri_ref_polarity")
GC_MS_ONLY = ("library_match", "library_score")
HRMS = ("mz_obs", "adduct", "mass_error_ppm")
LC_MS_ONLY = (*HRMS, "msms_match")
ISOLATION_ONLY = ("nmr_experiments", "nmr_solvent", "purity_percent", "novelty", "literature_doi",
                  "optical_rotation", "ecd", "ccdc", "configuration_type", "configuration")
EVIDENCE = (*COMMON, *GC_ONLY, *GC_MS_ONLY, *LC_MS_ONLY, *ISOLATION_ONLY)
TEXT_LIMITS = {"ri_ref_source": 200, "library_match": 200, "adduct": 40, "msms_match": 200,
               "standard_reference": 300, "data_accessions": 500, "nmr_solvent": 100, "optical_rotation": 200,
               "ecd": 300, "configuration": 300}
CSV_COLUMNS = ("feature", "value", "confidence", "status", *IDENTIFIERS, *EVIDENCE)


def allowed_columns(technique: str | None) -> set[str]:
    allowed = set(COMMON) | set(IDENTIFIERS)
    if technique in GC_TECHNIQUES:
        allowed |= set(GC_ONLY)
    if technique == "GC-MS":
        allowed |= set(GC_MS_ONLY)
    if technique in LC_MS_TECHNIQUES:
        allowed |= set(LC_MS_ONLY)
    if technique == ISOLATION:
        allowed |= set(HRMS) | set(ISOLATION_ONLY)
    return allowed


def _choice(raw: dict, name: str, choices: dict, where: str, label: str):
    value = choices.get(" ".join(raw[name].replace("_", " ").casefold().split()))
    if value is None:
        raise ValueError(f"{where}: {name} must be {label}.")
    return value


def _nmr_experiments(text: str, where: str) -> str:
    found = set()
    for token in re.split(r"[;,/]", text):
        key = re.sub(r"[\s\-{}^,]", "", token.translate(SUPERSCRIPTS).casefold()).removesuffix("nmr")
        if not key:
            continue
        if key not in NMR_EXPERIMENTS:
            raise ValueError(f"{where}: unknown NMR experiment {token.strip()!r}. Use names such as 1H, 13C, DEPT, "
                             "COSY, HSQC, HMBC, NOESY or ROESY.")
        found.add(NMR_EXPERIMENTS[key])
    return ";".join(item for item in NMR_ORDER if item in found)


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
    structure = None
    if "smiles" in raw:
        try:
            structure = parse_structure(raw["smiles"])
        except StructureError as error:
            raise ValueError(f"{where}: {error}") from error
        if identifiers.get("inchikey", structure["inchikey"]) != structure["inchikey"]:
            raise ValueError(f"{where}: the InChIKey does not match the structure given as SMILES "
                             f"({structure['inchikey']}).")
        identifiers["smiles"], identifiers["inchikey"] = structure["smiles"], structure["inchikey"]

    fields, warnings = {}, []
    for name in ("rt_min", "sd", "ri_exp", "ri_ref", "library_score", "mz_obs", "purity_percent"):
        if name in raw:
            fields[name] = _number(raw[name], name, where, minimum=0)
    if fields.get("purity_percent", 0) > 100:
        raise ValueError(f"{where}: purity_percent is out of range.")
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
                if " ".join(token.split()).casefold() not in ID_BASIS:
                    raise ValueError(f"{where}: unknown identification basis {token.strip()!r}. Use RI, MS, standard, "
                                     "co-injection, MS/MS, HRMS, NMR, X-ray, ECD or literature.")
                basis.add(ID_BASIS[" ".join(token.split()).casefold()])
        fields["id_basis"] = ";".join(item for item in ID_BASIS_ORDER if item in basis)
    if "id_level" in raw:
        level = int(_number(raw["id_level"], "id_level", where, integer=True, minimum=1))
        if level > 4:
            raise ValueError(f"{where}: id_level must be an MSI level from 1 to 4.")
        if level == 1 and not basis & (LEVEL_ONE_ISOLATION if technique == ISOLATION else LEVEL_ONE):
            raise ValueError(f"{where}: MSI level 1 requires identification against a reference standard or by "
                             "co-injection" + (", or structure elucidation by NMR or X-ray." if technique == ISOLATION
                                               else "."))
        fields["id_level"] = level
    if "standard_source" in raw:
        fields["standard_source"] = _choice(raw, "standard_source", STANDARD_SOURCES, where,
                                            "commercial, synthesized, isolated or gift")
    if ("standard_source" in fields or "standard_reference" in fields) and not basis & AUTHENTIC:
        raise ValueError(f"{where}: give the standard's source and reference only when the identification basis "
                         "includes standard or co-injection.")
    if "novelty" in raw:
        fields["novelty"] = _choice(raw, "novelty", NOVELTY, where, "new or known")
    if "configuration_type" in raw:
        fields["configuration_type"] = _choice(raw, "configuration_type", CONFIGURATION_TYPES, where,
                                               "absolute, relative or not determined")
    if "nmr_experiments" in raw:
        fields["nmr_experiments"] = _nmr_experiments(raw["nmr_experiments"], where)
    if "literature_doi" in raw:
        doi = DOI.match(raw["literature_doi"])
        if doi is None or len(doi.group(1)) > 200:
            raise ValueError(f"{where}: literature_doi must be a DOI such as 10.1021/np000000a.")
        fields["literature_doi"] = doi.group(1)
    if "ccdc" in raw:
        ccdc = CCDC.match(raw["ccdc"])
        if ccdc is None:
            raise ValueError(f"{where}: ccdc must be a CCDC deposition number such as CCDC 1234567.")
        fields["ccdc"] = f"CCDC {ccdc.group(1)}"
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
    warnings += structure_warnings(where, structure, fields, identifiers)
    return identifiers, fields, warnings


def structure_warnings(where: str, structure: dict | None, fields: dict, identifiers: dict) -> list[str]:
    """Checks of an isolated compound's record that an author should look at, but that may be right."""
    warnings = []
    if structure is not None:
        if fields.get("configuration_type") == "absolute" and structure["unassigned_stereocentres"]:
            warnings.append(f"{where}: absolute configuration is stated, but {structure['unassigned_stereocentres']} "
                            "stereocentre(s) are not specified in the SMILES.")
        if "mz_obs" in fields and fields.get("adduct"):
            expected = expected_mz(structure["monoisotopic_mass"], fields["adduct"])
            if expected is not None and abs(mass_error_ppm(fields["mz_obs"], expected)) > HRMS_TOLERANCE_PPM:
                warnings.append(f"{where}: observed m/z {fields['mz_obs']:g} differs from {expected:.4f} expected for "
                                f"{structure['molecular_formula']} {fields['adduct']} by "
                                f"{mass_error_ppm(fields['mz_obs'], expected):.1f} ppm.")
    if fields.get("novelty") == "known" and "literature_doi" not in fields:
        warnings.append(f"{where}: give the literature reference (literature_doi) a known compound was compared with.")
    if fields.get("novelty") == "new" and "smiles" not in identifiers:
        warnings.append(f"{where}: give the structure of a new compound as SMILES.")
    return warnings


def check_values(rows: list[dict], basis: str) -> list[str]:
    """Refuse a profile with no measured value. A percentage total above 100% is only a warning:
    tables can legitimately exceed it (rounding, co-eluting or separately integrated peaks)."""
    if not any(row["value"] is not None for row in rows):
        raise ValueError("Include at least one measured feature.")
    total = sum(row["value"] or 0 for row in rows)
    if basis == "peak_area_percent" and total > 100.5:
        return [f"Peak-area percentages total {total:g}%. Check that no summary or total rows were included."]
    return []


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
    warnings += check_values(rows, basis)
    return source, rows, warnings
