"""Analysis-ready CSV exports of released profiles, in long or wide format."""

import csv
from io import StringIO

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, Profile
from app.chemistry.repository import ChemistryRepository
from app.chemistry.sample_links import redetermined

MAX_EXPORT_PROFILES = 500
PROFILE_COLUMNS = ("study_id", "profile_id", "sample_code", "plant_part", "material_state", "batch_code",
                   "preparation_kind", "yield_percent", "run_code", "technique", "analytical_method",
                   "measurement_basis", "unit", "voucher_ids", "voucher_roles", "taxa", "redetermined")
MEASUREMENT_COLUMNS = ("feature", "cid", "compound_title", "molecular_formula", "inchikey", "status", "value",
                       "qualifier", "sd", "n", "confidence", "rt_min", "ri_exp", "ri_ref", "ri_ref_source", "id_basis",
                       "id_level", "library_match", "library_score", "mz_obs", "adduct", "mass_error_ppm")
WIDE_CELL = {"trace": "tr", "<LOQ": "<LOQ"}


def _text(value):
    if value is None:
        return ""
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, float):
        return f"{value:.15g}"
    return value


def _profile_fields(profile, preparation, sample, links):
    taxa = [taxon_name or voucher.subnomen or "" for _, voucher, taxon_name in links]
    return {
        "study_id": sample.study_id, "profile_id": profile.id, "sample_code": sample.code,
        "plant_part": sample.plant_part, "material_state": sample.material_state,
        "batch_code": preparation.batch_code, "preparation_kind": preparation.kind,
        "yield_percent": preparation.yield_percent, "run_code": profile.run_code, "technique": profile.technique,
        "analytical_method": profile.analytical_method, "measurement_basis": profile.measurement_basis,
        "unit": profile.unit, "voucher_ids": ";".join(link.specimen_id for link, _, _ in links),
        "voucher_roles": ";".join(link.role for link, _, _ in links), "taxa": ";".join(taxa),
        "redetermined": any(redetermined(link, voucher) for link, voucher, _ in links),
    }


def wide_key(measurement) -> tuple:
    """Linked compounds are keyed by CID; unlinked ones by name and experimental RI."""
    if measurement.cid is not None:
        return (0, measurement.cid, f"cid:{measurement.cid}")
    label = f"name:{measurement.feature}" + (f" @RI {measurement.ri_exp:g}" if measurement.ri_exp is not None else "")
    return (1, label.casefold(), label)


def _wide_cell(measurement) -> str:
    if measurement.status == "not_detected":
        return "nd"
    if measurement.status == "not_measured":
        return ""
    if measurement.value is None:
        return WIDE_CELL.get(measurement.qualifier, "")
    return _text(measurement.value)


class ExportService:
    def __init__(self, repository: ChemistryRepository):
        self.repository = repository

    def _records(self, profile_ids: list[str] | None, study_id: str | None):
        query = self.repository._released_profiles()
        if study_id is not None:
            query = query.where(LabSample.study_id == study_id)
        if profile_ids:
            if len(set(profile_ids)) > MAX_EXPORT_PROFILES:
                raise ChemistryError(422, f"Export at most {MAX_EXPORT_PROFILES} profiles at a time.")
            query = query.where(Profile.id.in_(set(profile_ids)))
        if not profile_ids and study_id is None:
            raise ChemistryError(422, "Choose released profiles or a study to export.")
        # The same order as the public study listing, so exports are reproducible.
        records = self.repository.db.execute(
            query.order_by(LabSample.study_id, LabSample.code, Profile.run_code, Profile.id)
            .limit(MAX_EXPORT_PROFILES + 1)).all()
        if len(records) > MAX_EXPORT_PROFILES:
            raise ChemistryError(422, f"Export at most {MAX_EXPORT_PROFILES} profiles at a time.")
        if profile_ids:
            missing = sorted(set(profile_ids) - {profile.id for profile, _, _ in records})
            if missing:
                raise ChemistryError(404, "These profiles are not released: " + ", ".join(missing))
        if not records:
            raise ChemistryError(404, "No released profiles to export.")
        links = self.repository.list_sample_links(sorted({sample.id for _, _, sample in records}))
        measurements = {profile.id: [] for profile, _, _ in records}
        for row, compound in self.repository.list_measurements(list(measurements)):
            measurements[row.profile_id].append((row, compound))
        return records, links, measurements

    def long(self, profile_ids=None, study_id=None) -> str:
        records, links, measurements = self._records(profile_ids, study_id)
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow((*PROFILE_COLUMNS, *MEASUREMENT_COLUMNS))
        for profile, preparation, sample in records:
            fields = _profile_fields(profile, preparation, sample, links[sample.id])
            for row, compound in measurements[profile.id]:
                values = {name: getattr(row, name, None) for name in MEASUREMENT_COLUMNS}
                values.update(compound_title=compound.title if compound else None,
                              molecular_formula=compound.molecular_formula if compound else None,
                              inchikey=compound.inchikey if compound else None)
                writer.writerow([_text(fields[name]) for name in PROFILE_COLUMNS]
                                + [_text(values[name]) for name in MEASUREMENT_COLUMNS])
        return output.getvalue()

    def wide(self, profile_ids=None, study_id=None) -> str:
        records, links, measurements = self._records(profile_ids, study_id)
        keys, cells = {}, {}
        for profile, _, _ in records:
            row = {}
            for measurement, _ in measurements[profile.id]:
                order, sort_key, label = wide_key(measurement)
                if label in row:
                    raise ChemistryError(409, f"Profile {profile.id} has two measurements for {label}. "
                                              "Correct the compound assignment or use the long format.")
                row[label] = _wide_cell(measurement)
                keys[label] = (order, sort_key)
            cells[profile.id] = row
        columns = sorted(keys, key=keys.get)
        output = StringIO(newline="")
        writer = csv.writer(output, lineterminator="\r\n")
        writer.writerow((*PROFILE_COLUMNS, *columns))
        for profile, preparation, sample in records:
            fields = _profile_fields(profile, preparation, sample, links[sample.id])
            writer.writerow([_text(fields[name]) for name in PROFILE_COLUMNS]
                            + [cells[profile.id].get(column, "") for column in columns])
        return output.getvalue()
