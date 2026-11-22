"""Turn an author's results table into profiles: assign columns, preview, review PubChem matches, confirm."""

import csv
from contextlib import ExitStack
from copy import deepcopy
from hashlib import sha256
from io import StringIO
from pathlib import PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from sqlalchemy import select

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import ImportTemplate, LabSample, Preparation, Profile, SpreadsheetImport
from app.chemistry.names import name_key
from app.chemistry.pubchem import PubChemUnavailable
from app.chemistry.sample_links import utc_now
from app.chemistry.schemas.import_schemas import AssignmentIn, RowReviewIn
from app.db import lock_for_update
from app.file_storage import FILES_ROOT, archive_member, store_upload
from app.users.models import User

from .compounds import CompoundRegistry, candidate_summary
from .chemistry_services import validated_run
from .profile_import import CSV_COLUMNS, check_values, parse_evidence
from .spreadsheet import (MAX_BYTES, MAX_ROWS, MAX_SAMPLES, PREVIEW_ROWS, cell_ref, evidence_text, is_summary,
                          parse_number, parse_value, read_table)

# Row-level columns, validated exactly as the per-run CSV validates them (technique-specific ones included).
EVIDENCE_ROLES = {"rt": "rt_min", "ri_exp": "ri_exp", "ri_ref": "ri_ref", "ri_ref_source": "ri_ref_source",
                  "id_basis": "id_basis", "id_level": "id_level", "cid": "cid", "cas": "cas", "inchikey": "inchikey",
                  "n": "n", "library_match": "library_match", "library_score": "library_score",
                  "mz_obs": "mz_obs", "adduct": "adduct", "mass_error_ppm": "mass_error_ppm", "msms_match": "msms_match"}
CONFIDENCE_BY_LEVEL = {1: "identified", 2: "annotated", 3: "tentative", 4: "unknown"}
MATCH_BATCH = 25
DECIDED = {"confirmed", "unidentified"}
MAX_CANDIDATES = 5


class OfflinePubChem:
    """Used while building a preview: matching that needs PubChem waits for the batch step."""

    def compounds(self, namespace, identifier):
        raise PubChemUnavailable("deferred")

    def same_connectivity(self, cid):
        raise PubChemUnavailable("deferred")


def _slim(record: dict) -> dict:
    return {**record, "synonyms": record["synonyms"][:20]}


class ImportService:
    def __init__(self, chemistry, registry: CompoundRegistry):
        self.chemistry = chemistry
        self.repository = chemistry.repository
        self.db = chemistry.repository.db
        self.registry = registry
        self.offline = CompoundRegistry(self.db, OfflinePubChem())

    # Access ---------------------------------------------------------------------------------------------------

    def _import_for_actor(self, import_id: str, actor: User, *, draft=True) -> SpreadsheetImport:
        record = self.db.get(SpreadsheetImport, import_id)
        if record is None or (not actor.is_superuser and record.owner_id != actor.user_id):
            raise ChemistryError(404, "Import not found.")
        self.chemistry._study_for_actor(record.study_id, actor)
        if draft and record.status != "draft":
            raise ChemistryError(409, "This import has already been confirmed.")
        return record

    def _table(self, record: SpreadsheetImport):
        try:
            with archive_member(FILES_ROOT, record.source_path).open("rb") as source:
                content = source.read(MAX_BYTES + 1)
        except (OSError, ValueError) as error:
            raise ChemistryError(409, "The uploaded spreadsheet is missing or unreadable.") from error
        if sha256(content).hexdigest() != record.source_sha256:
            raise ChemistryError(409, "The uploaded spreadsheet failed SHA-256 verification.")
        return read_table(content, record.source_kind)

    # Upload ---------------------------------------------------------------------------------------------------

    def create(self, study_id: str, source_file: BinaryIO, source_name: str | None, actor: User):
        self.chemistry._study_for_actor(study_id, actor)
        filename = PurePosixPath((source_name or "results").replace("\\", "/")).name[:200] or "results"
        kind = filename.rsplit(".", 1)[-1].casefold() if "." in filename else ""
        if kind not in ("xlsx", "csv"):
            raise ChemistryError(422, "Upload the results table as .xlsx or .csv.")
        content = source_file.read(MAX_BYTES + 1)
        try:
            sheets = read_table(content, kind)
        except ValueError as error:
            raise ChemistryError(422, str(error)) from error
        if not any(sheets.values()):
            raise ChemistryError(422, "The table is empty.")
        record = SpreadsheetImport(study_id=study_id, owner_id=actor.user_id, status="draft", created_at=utc_now(),
                                   source_name=filename, source_kind=kind,
                                   source_path=(FILES_ROOT / f"{uuid4().hex}.{kind}").as_posix(),
                                   source_sha256=sha256(content).hexdigest())
        try:
            with store_upload(archive_member(FILES_ROOT, record.source_path), content):
                self.repository.save(record)
        except (OSError, ValueError) as error:
            raise ChemistryError(500, "Could not store the uploaded spreadsheet.") from error
        return record, sheets

    def list_for_study(self, study_id: str, actor: User):
        self.chemistry._study_for_actor(study_id, actor)
        query = select(SpreadsheetImport).where(SpreadsheetImport.study_id == study_id)
        if not actor.is_superuser:
            query = query.where(SpreadsheetImport.owner_id == actor.user_id)
        return self.db.scalars(query.order_by(SpreadsheetImport.created_at.desc())).all()

    def sheet_preview(self, import_id: str, actor: User):
        record = self._import_for_actor(import_id, actor, draft=False)
        return record, {name: rows[:PREVIEW_ROWS] for name, rows in self._table(record).items()}

    # Assignment and preview -------------------------------------------------------------------------------------

    def _preparations(self, study_id: str):
        rows = self.db.execute(select(Preparation, LabSample).join(LabSample)
                               .where(LabSample.study_id == study_id)).all()
        return {preparation.id: (preparation, sample) for preparation, sample in rows}

    def analyse(self, record: SpreadsheetImport, data: AssignmentIn):
        """Parse the table under an assignment. Returns (preview, review), without writing anything."""
        sheets = self._table(record)
        if data.sheet not in sheets:
            raise ChemistryError(422, f"The workbook has no sheet named {data.sheet!r}.")
        table = sheets[data.sheet]
        if data.header_row > len(table):
            raise ChemistryError(422, "The header row is past the end of the sheet.")
        header = table[data.header_row - 1]
        width = len(header)
        columns = {}
        for column in data.columns:
            if column.index >= width:
                raise ChemistryError(422, f"Column {cell_ref(column.index, data.header_row)} is outside the table.")
            if column.index in columns:
                raise ChemistryError(422, f"Column {cell_ref(column.index, data.header_row)} is assigned twice.")
            columns[column.index] = column
        names = [column for column in columns.values() if column.role == "name"]
        samples = [column for column in columns.values() if column.role == "sample"]
        if len(names) != 1:
            raise ChemistryError(422, "Assign exactly one compound name column.")
        if not samples or len(samples) > MAX_SAMPLES:
            raise ChemistryError(422, f"Assign between one and {MAX_SAMPLES} sample value columns.")
        for role in EVIDENCE_ROLES:
            if sum(column.role == role for column in columns.values()) > 1:
                raise ChemistryError(422, f"Assign at most one {role} column.")
        sd_columns = {}
        for column in columns.values():
            if column.role == "sd":
                if column.sd_for is None or column.sd_for not in columns or columns[column.sd_for].role != "sample":
                    raise ChemistryError(422, f"Pair SD column {cell_ref(column.index, data.header_row)} with a sample column.")
                if column.sd_for in sd_columns:
                    raise ChemistryError(422, "Pair at most one SD column with each sample column.")
                sd_columns[column.sd_for] = column.index

        errors, warnings = [], []
        preparations = self._preparations(record.study_id)
        by_code = {}
        for preparation, sample in preparations.values():
            by_code.setdefault(sample.code.casefold(), []).append(preparation)
        existing = {(preparation_id, code) for preparation_id, code in self.db.execute(
            select(Profile.preparation_id, Profile.run_code).where(Profile.preparation_id.in_(list(preparations))))}
        profiles, run_codes = [], set()
        for column in sorted(samples, key=lambda item: item.index):
            heading = header[column.index]
            heading = evidence_text(heading) or cell_ref(column.index, data.header_row)
            preparation_id = column.preparation_id
            if preparation_id is None and len(by_code.get(heading.casefold(), [])) == 1:
                preparation_id = by_code[heading.casefold()][0].id
            settings = data.settings.model_dump() | {key: value for key, value in (
                column.overrides.model_dump() if column.overrides else {}).items() if value is not None}
            run_code = (column.run_code or heading)[:80]
            where = f"Column {cell_ref(column.index, data.header_row)} ({heading})"
            if preparation_id not in preparations:
                errors.append(f"{where}: choose the lab sample preparation this column belongs to.")
            elif (preparation_id, run_code) in existing or (preparation_id, run_code) in run_codes:
                errors.append(f"{where}: run code {run_code!r} is already used for this preparation.")
            run_codes.add((preparation_id, run_code))
            try:
                settings["run_metadata"] = validated_run(settings["technique"], settings["run_metadata"])
            except ChemistryError as error:
                errors.append(f"{where}: {error}")
                settings["run_metadata"] = {}
            if settings["measurement_basis"] == "peak_area_percent" and settings["unit"] != "%":
                errors.append(f"{where}: use % as the unit for peak-area percentages.")
            profiles.append({"index": column.index, "header": heading, "preparation_id": preparation_id,
                             "run_code": run_code, "settings": settings, "sd_index": sd_columns.get(column.index)})

        name_index = names[0].index
        evidence_columns = {EVIDENCE_ROLES[column.role]: column.index for column in columns.values()
                            if column.role in EVIDENCE_ROLES}
        rows, seen, footnotes = [], {}, []
        previous = (record.review or {}).get("rows", {}) if record.assignment else {}
        decisions = {row["key"]: row for row in previous.values() if row["status"] in DECIDED}
        review = {}
        data_rows = table[data.header_row:]
        if len([row for row in data_rows if any(cell is not None for cell in row)]) > MAX_ROWS:
            raise ChemistryError(422, f"A table can have at most {MAX_ROWS} compound rows.")
        for offset, cells in enumerate(data_rows):
            number = data.header_row + 1 + offset
            cells = cells + [None] * (width - len(cells))
            name = evidence_text(cells[name_index]).strip()
            if not name:
                if any(cells[profile["index"]] is not None for profile in profiles):
                    errors.append(f"Row {number} has values but no compound name.")
                continue
            summary = is_summary(name)
            included = data.row_overrides.get(number, not summary)
            row = {"row": number, "name": name, "summary": summary, "included": included, "errors": [],
                   "values": {}, "evidence": {}}
            rows.append(row)
            if not included:
                continue
            if len(name) > 160:
                row["errors"].append("The compound name is longer than 160 characters.")
            key = name_key(name)
            if key in seen:
                row["errors"].append(f"The same compound name is also on row {seen[key]}.")
            seen[key] = number
            raw = {field: evidence_text(cells[index]) for field, index in evidence_columns.items()}
            if data.settings.ri_ref_polarity and raw.get("ri_ref"):
                raw["ri_ref_polarity"] = data.settings.ri_ref_polarity
            identifiers = {}
            for profile in profiles:
                settings = profile["settings"]
                try:
                    identifiers, fields, row_warnings = parse_evidence(
                        raw, f"Row {number}", settings["technique"], settings["run_metadata"],
                        data.settings.ri_tolerance)
                except ValueError as error:
                    row["errors"].append(f"{profile['header']}: {error}")
                    continue
                row["evidence"] = fields
                warnings.extend(warning for warning in row_warnings if warning not in warnings)
            for profile in profiles:
                ref = cell_ref(profile["index"], number)
                try:
                    parsed = parse_value(cells[profile["index"]])
                    if profile["sd_index"] is not None and cells[profile["sd_index"]] is not None:
                        parsed["sd"], sd_marks = parse_number(cells[profile["sd_index"]])
                        parsed["marks"] = parsed["marks"] or sd_marks
                except ValueError:
                    row["errors"].append(f"{ref}: {cells[profile['index']]!r} is not a number, tr, nd or –.")
                    continue
                if parsed.pop("marks"):
                    footnotes.append(ref)
                value = parsed["value"]
                if value is not None and profile["settings"]["measurement_basis"] == "peak_area_percent" and value > 100:
                    row["errors"].append(f"{ref}: a percentage above 100.")
                row["values"][str(profile["index"])] = parsed
            row["identifiers"] = identifiers
            review[str(number)] = self._propose(record.owner_id, name, key, identifiers, decisions.get(key))

        for profile in profiles:
            values = [row["values"].get(str(profile["index"])) for row in rows if row["included"]]
            values = [value for value in values if value]
            profile["total"] = round(sum(value["value"] or 0 for value in values), 6)
            profile["detected"] = sum(value["status"] == "measured" for value in values)
            try:
                check_values([value for value in values], profile["settings"]["measurement_basis"])
            except ValueError as error:
                errors.append(f"{profile['header']}: {error}")
        if footnotes:
            warnings.append(f"Footnote marks were removed from {len(footnotes)} cells: {', '.join(footnotes[:30])}"
                            + (" …" if len(footnotes) > 30 else ""))
        summaries = [row["row"] for row in rows if row["summary"] and not row["included"]]
        if summaries:
            warnings.append("Summary rows were left out: " + ", ".join(map(str, summaries)) + ".")
        errors += [f"Row {row['row']}: {problem}" for row in rows for problem in row["errors"]]
        return {"profiles": profiles, "rows": rows, "errors": errors, "warnings": warnings}, {"rows": review}

    def _propose(self, owner_id, name, key, identifiers, decision):
        if decision is not None:
            return decision
        base = {"name": name, "key": key, "identifiers": identifiers}
        try:
            if identifiers:
                record, method = self.offline.lookup_identifiers(**identifiers)
                return {**base, "status": "needs_review", "method": method, "record": _slim(record),
                        "candidates": [_slim(record)]}
            match = self.offline.match_name(owner_id, name)
        except ChemistryError as error:
            if error.code != 503:
                return {**base, "status": "unmatched", "method": None, "record": None, "candidates": [],
                        "problem": str(error)}
            return {**base, "status": "pending", "method": None, "record": None, "candidates": []}
        if match["proposal"] is None:
            return {**base, "status": "pending", "method": None, "record": None, "candidates": []}
        return {**base, "status": match["status"], "method": match["method"], "record": _slim(match["proposal"]),
                "candidates": [_slim(item) for item in match["candidates"][:MAX_CANDIDATES]]}

    def assign(self, import_id: str, data: AssignmentIn, actor: User):
        record = self._import_for_actor(import_id, actor)
        preview, review = self.analyse(record, data)
        record.assignment = data.model_dump(mode="json")
        record.review = review
        self.repository.save(record)
        return record, preview

    def preview(self, import_id: str, actor: User):
        record = self._import_for_actor(import_id, actor, draft=False)
        if not record.assignment:
            return record, None
        preview, _ = self.analyse(record, AssignmentIn.model_validate(record.assignment))
        return record, preview

    # PubChem matching and review ------------------------------------------------------------------------------

    def match_pending(self, import_id: str, actor: User, limit: int = MATCH_BATCH):
        """Look up the next pending rows in PubChem. Call repeatedly until nothing is pending."""
        record = self._import_for_actor(import_id, actor)
        # A copy: JSON columns only save on reassignment, and in-place edits would hide the change.
        review = deepcopy(record.review or {"rows": {}})
        pending = [number for number, row in review["rows"].items() if row["status"] == "pending"]
        problem = None
        for number in pending[:limit]:
            row = review["rows"][number]
            try:
                if row["identifiers"]:
                    found, method = self.registry.lookup_identifiers(**row["identifiers"])
                    update = {"status": "needs_review", "method": method, "record": _slim(found),
                              "candidates": [_slim(found)]}
                else:
                    match = self.registry.match_name(record.owner_id, row["name"])
                    if match.get("problem"):
                        raise ChemistryError(503, match["problem"])
                    update = {"status": match["status"] if match["proposal"] else "unmatched",
                              "method": match["method"], "record": match["proposal"] and _slim(match["proposal"]),
                              "candidates": [_slim(item) for item in match["candidates"][:MAX_CANDIDATES]]}
            except ChemistryError as error:
                if error.code == 503:
                    problem = str(error)
                    break
                update = {"status": "unmatched", "method": None, "record": None, "candidates": [],
                          "problem": str(error)}
            review["rows"][number] = {**row, **update}
        record.review = review
        self.repository.save(record)
        remaining = sum(row["status"] == "pending" for row in review["rows"].values())
        return {"pending": remaining, "problem": problem, "review": review_summary(record.review)}

    def review_row(self, import_id: str, row_number: int, data: RowReviewIn, actor: User):
        record = self._import_for_actor(import_id, actor)
        rows = deepcopy((record.review or {}).get("rows", {}))
        row = rows.get(str(row_number))
        if row is None:
            raise ChemistryError(404, "This row is not part of the import.")
        if data.action == "accept":
            if not row["record"]:
                raise ChemistryError(409, "There is no proposed match to accept. Choose a compound or mark the row unidentified.")
            row = {**row, "status": "confirmed"}
        elif data.action == "unidentified":
            row = {**row, "status": "unidentified", "record": None}
        elif data.action == "choose":
            if data.cid is None:
                raise ChemistryError(422, "Give the CID of the chosen compound.")
            chosen = next((item for item in row["candidates"] if item["cid"] == data.cid), None)
            if chosen is None:
                found = self.registry.search(str(data.cid), "cid")
                if not found:
                    raise ChemistryError(404, f"PubChem has no compound with CID {data.cid}.")
                chosen = found[0]
            row = {**row, "status": "confirmed", "method": "manual", "record": _slim(chosen),
                   "candidates": row["candidates"] if chosen in row["candidates"] else [_slim(chosen), *row["candidates"]][:MAX_CANDIDATES]}
        else:
            if not row["record"]:
                raise ChemistryError(409, "Choose a compound before switching to its parent.")
            parent = self.registry.parent(row["record"]["cid"], row["record"])
            row = {**row, "status": "confirmed", "method": "parent", "record": _slim(parent)}
        rows[str(row_number)] = row
        record.review = {"rows": rows}
        self.repository.save(record)
        return review_row_summary(str(row_number), row)

    # Templates ------------------------------------------------------------------------------------------------

    def list_templates(self, actor: User):
        return self.db.scalars(select(ImportTemplate).where(ImportTemplate.owner_id == actor.user_id)
                               .order_by(ImportTemplate.name)).all()

    def apply_template(self, import_id: str, template_id: str, sheet: str | None, actor: User):
        """An assignment for this upload from a saved layout: columns are found by their header text."""
        record = self._import_for_actor(import_id, actor)
        template = self.db.get(ImportTemplate, template_id)
        if template is None or template.owner_id != actor.user_id:
            raise ChemistryError(404, "Template not found.")
        layout = template.layout
        sheets = self._table(record)
        sheet = sheet or (layout["sheet"] if layout["sheet"] in sheets else next(iter(sheets)))
        table = sheets.get(sheet) or []
        if layout["header_row"] > len(table):
            raise ChemistryError(422, "The saved header row is past the end of this sheet.")
        header = [evidence_text(cell).strip().casefold() for cell in table[layout["header_row"] - 1]]
        columns, missing = [], []
        for column in layout["columns"]:
            heading = column["header"].casefold()
            if heading not in header:
                if column["role"] != "sample":
                    missing.append(column["header"])
                continue
            entry = {"index": header.index(heading), "role": column["role"]}
            if column.get("sd_for_header"):
                if column["sd_for_header"].casefold() not in header:
                    continue
                entry["sd_for"] = header.index(column["sd_for_header"].casefold())
            columns.append(entry)
        assigned = {column["index"] for column in columns}
        sample_like = layout.get("unassigned_role", "sample")
        for index, heading in enumerate(header):
            if index not in assigned and heading and sample_like == "sample":
                columns.append({"index": index, "role": "sample"})
        return {"sheet": sheet, "header_row": layout["header_row"], "columns": sorted(columns, key=lambda c: c["index"]),
                "settings": layout["settings"], "row_overrides": {}, "missing_headers": missing}

    def _save_template(self, owner_id: str, name: str, assignment: dict, header: list):
        template = self.db.scalar(select(ImportTemplate).where(ImportTemplate.owner_id == owner_id,
                                                               ImportTemplate.name == name))
        if template is None:
            template = ImportTemplate(owner_id=owner_id, name=name, created_at=utc_now())
            self.db.add(template)
        text = lambda index: evidence_text(header[index]).strip()  # noqa: E731
        template.layout = {
            "sheet": assignment["sheet"], "header_row": assignment["header_row"],
            "settings": assignment["settings"],
            # Sample columns change between tables; any column not listed here is treated as a sample column.
            "columns": [{"header": text(column["index"]), "role": column["role"],
                         **({"sd_for_header": text(column["sd_for"])} if column.get("sd_for") is not None else {})}
                        for column in assignment["columns"] if column["role"] not in ("sample",)],
            "unassigned_role": "sample",
        }

    # Confirmation ---------------------------------------------------------------------------------------------

    def confirm(self, import_id: str, actor: User):
        lock_for_update(self.db, self.db.query(SpreadsheetImport).filter_by(id=import_id)).first()
        record = self._import_for_actor(import_id, actor)
        if not record.assignment:
            raise ChemistryError(409, "Assign the columns first.")
        data = AssignmentIn.model_validate(record.assignment)
        preview, _ = self.analyse(record, data)
        if preview["errors"]:
            raise ChemistryError(422, "Fix the problems shown in the preview first: " + " ".join(preview["errors"][:5]))
        review = record.review["rows"]
        open_rows = [row["row"] for row in preview["rows"] if row["included"]
                     and review.get(str(row["row"]), {}).get("status") not in DECIDED]
        if open_rows:
            raise ChemistryError(409, "Confirm a compound or mark the row unidentified for rows "
                                 + ", ".join(map(str, open_rows[:20])) + (" …" if len(open_rows) > 20 else "") + ".")
        included = {str(row["row"]) for row in preview["rows"] if row["included"]}
        registered = set()
        for number, row in review.items():
            if number in included and row["status"] == "confirmed":
                if row["record"]["cid"] not in registered:
                    self.registry.register(row["record"])
                    registered.add(row["record"]["cid"])
                # Confirmed choices become the author's aliases; existing measurements are never changed by them.
                self.registry.save_alias(record.owner_id, row["name"], row["record"]["cid"])
        created = []
        with ExitStack() as uploads:
            for profile in preview["profiles"]:
                rows = []
                for row in preview["rows"]:
                    if not row["included"]:
                        continue
                    cell = row["values"].get(str(profile["index"]))
                    decision = review[str(row["row"])]
                    evidence = dict(row["evidence"])
                    level = evidence.get("id_level")
                    rows.append({
                        "feature": row["name"], "value": cell["value"], "status": cell["status"],
                        "confidence": CONFIDENCE_BY_LEVEL.get(level, data.settings.confidence),
                        "cid": decision["record"]["cid"] if decision["status"] == "confirmed" else None,
                        "compound_match": decision["method"] if decision["status"] == "confirmed" else "unidentified",
                        **({"qualifier": cell["qualifier"]} if cell["qualifier"] else {}),
                        **({"sd": cell["sd"]} if cell.get("sd") is not None and cell["status"] == "measured" else {}),
                        **evidence,
                    })
                content = canonical_csv(rows).encode("utf-8")
                settings = profile["settings"]
                created.append(self.chemistry.store_profile(
                    profile["preparation_id"], profile["run_code"], settings["analytical_method"],
                    settings["measurement_basis"], settings["unit"], settings["technique"], settings["run_metadata"],
                    f"{PurePosixPath(record.source_name).stem[:150]}-{profile['header'][:40]}.csv", content,
                    content.decode("utf-8"), rows, uploads=uploads, import_id=record.id,
                    import_column=profile["header"][:200]))
            if data.save_template:
                header = self._table(record)[data.sheet][data.header_row - 1]
                self._save_template(record.owner_id, data.save_template, record.assignment, header)
            record.status, record.confirmed_at = "confirmed", utc_now()
            self.repository.save(record)
        return created


def canonical_csv(rows: list[dict]) -> str:
    """The per-profile CSV generated from a confirmed import; it re-imports to the same measurements."""
    output = StringIO(newline="")
    writer = csv.writer(output, lineterminator="\r\n")
    columns = [column for column in CSV_COLUMNS if column not in ("inchikey", "cas")]
    used = [column for column in columns if column in ("feature", "value", "confidence", "status")
            or any(row.get(column) is not None for row in rows)]
    writer.writerow(used)
    for row in rows:
        writer.writerow(["" if row.get(column) is None else
                         (f"{row[column]:.15g}" if isinstance(row[column], float) else row[column]) for column in used])
    return output.getvalue()


def review_row_summary(number: str, row: dict) -> dict:
    return {"row": int(number), "name": row["name"], "status": row["status"], "method": row["method"],
            "match": candidate_summary(row["record"]) if row.get("record") else None,
            "candidates": [candidate_summary(item) for item in row.get("candidates", [])],
            "problem": row.get("problem")}


def review_summary(review: dict | None) -> list[dict]:
    rows = (review or {}).get("rows", {})
    return [review_row_summary(number, row) for number, row in sorted(rows.items(), key=lambda item: int(item[0]))]
