from datetime import date
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, ValidationError, confloat, conint, constr, model_validator

Code = constr(strip_whitespace=True, min_length=1, max_length=80)
Identifier = constr(strip_whitespace=True, min_length=1, max_length=50)
Basis = Literal["concentration", "peak_area", "peak_area_percent", "isolated_mass"]
PlantPart = Literal["leaf", "flower", "inflorescence", "aerial parts", "stem", "root", "rhizome", "bark",
                    "fruit", "seed", "whole plant", "other"]
MaterialState = Literal["fresh", "air-dried", "oven-dried", "freeze-dried"]
VoucherRole = Literal["sampled_from_voucher", "same_individual", "same_population", "collected_alongside",
                      "cultivated_from", "reference_for_commercial_material"]
# "isolation": compounds isolated from a preparation, with their structures determined (NMR, HRMS, X-ray…).
Technique = Literal["GC-MS", "GC-FID", "LC-MS", "LC-MS/MS", "HPLC-DAD", "isolation"]
ISOLATED_UNITS = ("mg", "g", "µg")
VOUCHER_ROLES = get_args(VoucherRole)
MAX_SAMPLE_VOUCHERS = 20


def optional_text(max_length):
    return constr(strip_whitespace=True, min_length=1, max_length=max_length) | None


class StudyIn(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=200)
    description: constr(strip_whitespace=True, max_length=4000) = ""
    publication_id: str | None = Field(None, max_length=50)


class VoucherLinkIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    specimen_id: Identifier
    role: VoucherRole


class SampleIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    code: Code
    vouchers: list[VoucherLinkIn] = Field(min_length=1, max_length=MAX_SAMPLE_VOUCHERS)
    plant_part: PlantPart
    plant_part_note: optional_text(200) = None
    material_state: MaterialState | None = None
    collection_date: date | None = None
    phenological_stage: optional_text(100) = None
    site_specimen_id: Identifier | None = None
    field_loc_id: Identifier | None = None
    drying_notes: optional_text(1000) = None
    storage_notes: optional_text(1000) = None
    collection_notes: optional_text(200) = None

    @model_validator(mode="after")
    def consistent_links_and_site(self):
        linked = [link.specimen_id for link in self.vouchers]
        if len(set(linked)) != len(linked):
            raise ValueError("Link each voucher once.")
        if self.site_specimen_id and self.field_loc_id:
            raise ValueError("Give the collection site either as a linked voucher's site or as a field location.")
        if self.site_specimen_id and self.site_specimen_id not in linked:
            raise ValueError("The collection site voucher must be one of the linked vouchers.")
        if self.plant_part == "other" and not self.plant_part_note:
            raise ValueError("Describe the plant part when choosing other.")
        return self


class GCRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: optional_text(200) = None
    stationary_phase: optional_text(200) = None
    polarity_class: Literal["non-polar", "semi-polar", "polar"]
    temperature_programme: optional_text(1000) = None
    carrier_gas: optional_text(100) = None
    alkane_series: optional_text(200) = None
    ri_type: Literal["linear_temperature_programmed", "isothermal_kovats"] | None = None
    data_accessions: optional_text(500) = None


class LCRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: optional_text(200) = None
    mobile_phase: optional_text(500) = None
    gradient: optional_text(1000) = None
    ionisation_mode: Literal["ESI+", "ESI-", "APCI+", "APCI-", "APPI+", "APPI-"] | None = None
    mass_analyser: optional_text(100) = None
    data_accessions: optional_text(500) = None


class IsolationRun(BaseModel):
    """Conditions shared by the compounds of one isolation; each compound may add its own details."""
    model_config = ConfigDict(extra="forbid")

    isolation_procedure: optional_text(2000) = None
    nmr_spectrometer: optional_text(200) = None
    nmr_frequency_mhz: confloat(gt=0, le=2000, allow_inf_nan=False) | None = None
    nmr_solvent: optional_text(100) = None
    hrms_instrument: optional_text(200) = None
    hrms_ionisation: optional_text(40) = None
    data_accessions: optional_text(500) = None


def run_metadata_for(technique: str, data: dict | None) -> dict:
    """Validate run metadata for a technique; GC runs need the column polarity class for RI checks."""
    model = GCRun if technique in ("GC-MS", "GC-FID") else IsolationRun if technique == "isolation" else LCRun
    return model.model_validate(data or {}).model_dump(exclude_none=True)


def basis_problem(technique: str | None, basis: str, unit: str) -> str | None:
    """An isolation reports isolated amounts, and only an isolation does."""
    if (technique == "isolation") != (basis == "isolated_mass"):
        return ("Record isolated compounds with the isolation technique and the isolated-amount basis "
                "(and use that basis only for isolations).")
    if basis == "isolated_mass" and unit.replace("μ", "µ").replace("ug", "µg") not in ISOLATED_UNITS:
        return "Give isolated amounts in mg, g or µg."
    return None


class PreparationIn(BaseModel):
    # P1, P2… for the sample when left empty.
    batch_code: Code | None = None
    kind: Literal["extract", "essential_oil"]
    method_reference: constr(strip_whitespace=True, min_length=1, max_length=500)
    plant_material_mass_g: confloat(gt=0, allow_inf_nan=False) | None = None
    method_parameters: optional_text(1000) = None
    # An essential oil's yield is required before it is published, not when the preparation is created.
    yield_percent: confloat(ge=0, le=100, allow_inf_nan=False) | None = None


def run_problems(error: ValidationError) -> str:
    return "; ".join(f"{'.'.join(map(str, item['loc'])) or 'run metadata'}: {item['msg']}" for item in error.errors())


class RunPresetValues(BaseModel):
    """Saved run conditions: what the results-table settings and the run fields hold."""
    model_config = ConfigDict(extra="forbid")

    technique: Technique
    analytical_method: optional_text(120) = None
    measurement_basis: Basis | None = None
    unit: optional_text(40) = None
    run_metadata: dict | None = None

    @model_validator(mode="after")
    def valid_run(self):
        try:
            self.run_metadata = run_metadata_for(self.technique, self.run_metadata)
        except ValidationError as error:
            raise ValueError(f"Invalid run conditions for {self.technique}: {run_problems(error)}") from None
        return self


class PreparationPresetValues(BaseModel):
    """A saved preparation method. Batch code, mass and yield belong to each preparation."""
    model_config = ConfigDict(extra="forbid")

    kind: Literal["extract", "essential_oil"]
    method_reference: constr(strip_whitespace=True, min_length=1, max_length=500)
    method_parameters: optional_text(1000) = None


PRESET_VALUES = {"run": RunPresetValues, "preparation": PreparationPresetValues}


class ConditionPresetIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    kind: Literal["run", "preparation"]
    name: constr(strip_whitespace=True, min_length=1, max_length=120)
    values: dict

    @model_validator(mode="after")
    def valid_values(self):
        self.values = PRESET_VALUES[self.kind].model_validate(self.values).model_dump(exclude_none=True)
        return self


class SamplePreparationIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    sample_id: Identifier | None = None
    sample: SampleIn | None = None
    preparation: PreparationIn

    @model_validator(mode="after")
    def choose_sample(self):
        if (self.sample_id is None) == (self.sample is None):
            raise ValueError("Choose an existing sample or enter details for a new sample.")
        return self


class CompoundCorrectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cid: conint(gt=0, lt=2 ** 31) | None = None
    # A structure as SMILES or molfile; PubChem's CID is used when PubChem has the same InChIKey.
    smiles: constr(strip_whitespace=True, min_length=1, max_length=20000) | None = None
    reason: constr(strip_whitespace=True, min_length=1, max_length=1000)

    @model_validator(mode="after")
    def one_assignment(self):
        if self.cid is not None and self.smiles is not None:
            raise ValueError("Give either a CID or a structure, not both.")
        return self


class PublicState(BaseModel):
    is_public: bool


