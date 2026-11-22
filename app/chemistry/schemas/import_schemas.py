from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, constr, field_validator, model_validator

from .chemistry_schemas import Basis, Technique, optional_text

ISOLATION_METHOD = "Isolation and structure elucidation"

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
    # Worked out from the technique and the run's column unless given (older imports and the API give it).
    analytical_method: optional_text(120) = None
    confidence: constr(strip_whitespace=True, min_length=1, max_length=30) = "annotated"
    ri_tolerance: confloat(gt=0, le=500) = 20
    ri_ref_polarity: Literal["non-polar", "semi-polar", "polar"] | None = None

    @field_validator("analytical_method", "ri_ref_polarity", mode="before")
    @classmethod
    def blank_is_not_given(cls, value):
        # Pages from before these fields were removed send them empty.
        return None if isinstance(value, str) and not value.strip() else value

    @model_validator(mode="after")
    def method_for_technique(self):
        if self.analytical_method is None:
            self.analytical_method = method_label(self.technique, self.run_metadata)
        return self


def method_label(technique: str, run_metadata: dict | None) -> str:
    """The analytical method shown for a run: the technique, with the column where one is given."""
    if technique == "isolation":
        return ISOLATION_METHOD
    column = str((run_metadata or {}).get("column") or "").strip()
    return f"{technique}, {column}"[:120] if column else technique


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

    action: Literal["accept", "choose", "unidentified", "parent", "structure"]
    cid: conint(gt=0, lt=2 ** 31) | None = None
    # For "structure": a SMILES or molfile. PubChem's CID is used when it has the same InChIKey.
    smiles: constr(strip_whitespace=True, min_length=1, max_length=20000) | None = None
