from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, constr

from .chemistry_schemas import Basis, Technique, optional_text

ColumnRole = Literal["name", "rt", "ri_exp", "ri_ref", "ri_ref_source", "id_basis", "id_level", "cid", "cas",
                     "inchikey", "smiles", "n", "library_match", "library_score", "mz_obs", "adduct", "mass_error_ppm",
                     "msms_match", "standard_source", "standard_reference", "data_accessions", "nmr_experiments",
                     "nmr_solvent", "purity_percent", "novelty", "literature_doi", "optical_rotation", "ecd", "ccdc",
                     "configuration_type", "configuration", "sample", "sd", "ignore"]


class ProfileSettings(BaseModel):
    """Set once per upload; each sample column may override them."""
    model_config = ConfigDict(extra="forbid")

    technique: Technique | None = None
    measurement_basis: Basis | None = None
    unit: optional_text(40) = None
    analytical_method: optional_text(120) = None
    run_metadata: dict | None = None


class UploadSettings(ProfileSettings):
    technique: Technique
    measurement_basis: Basis
    unit: constr(strip_whitespace=True, min_length=1, max_length=40)
    analytical_method: constr(strip_whitespace=True, min_length=1, max_length=120)
    confidence: constr(strip_whitespace=True, min_length=1, max_length=30) = "annotated"
    ri_tolerance: confloat(gt=0, le=500) = 20
    ri_ref_polarity: Literal["non-polar", "semi-polar", "polar"] | None = None


class ColumnAssignment(BaseModel):
    model_config = ConfigDict(extra="forbid")

    index: conint(ge=0, lt=300)
    role: ColumnRole
    preparation_id: constr(strip_whitespace=True, min_length=1, max_length=50) | None = None
    run_code: optional_text(80) = None
    sd_for: conint(ge=0, lt=300) | None = None
    overrides: ProfileSettings | None = None


class AssignmentIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sheet: constr(min_length=1, max_length=100)
    header_row: conint(ge=1, le=1000)
    columns: list[ColumnAssignment] = Field(min_length=2, max_length=300)
    settings: UploadSettings
    # Sheet row number → include (True) or exclude (False); overrides summary-row detection.
    row_overrides: dict[int, bool] = Field(default_factory=dict)
    save_template: optional_text(120) = None


class RowReviewIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    action: Literal["accept", "choose", "unidentified", "parent"]
    cid: conint(gt=0, lt=2 ** 31) | None = None
