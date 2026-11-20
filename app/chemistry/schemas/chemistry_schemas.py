from datetime import date
from typing import Literal, get_args

from pydantic import BaseModel, ConfigDict, Field, confloat, conint, constr, model_validator

Code = constr(strip_whitespace=True, min_length=1, max_length=80)
Identifier = constr(strip_whitespace=True, min_length=1, max_length=50)
Basis = Literal["concentration", "peak_area", "peak_area_percent"]
PlantPart = Literal["leaf", "flower", "inflorescence", "aerial parts", "stem", "root", "rhizome", "bark",
                    "fruit", "seed", "whole plant", "other"]
MaterialState = Literal["fresh", "air-dried", "oven-dried", "freeze-dried"]
VoucherRole = Literal["sampled_from_voucher", "same_individual", "same_population", "collected_alongside",
                      "cultivated_from", "reference_for_commercial_material"]
Technique = Literal["GC-MS", "GC-FID", "LC-MS", "LC-MS/MS", "HPLC-DAD"]
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
    material_state: MaterialState
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


class LCRun(BaseModel):
    model_config = ConfigDict(extra="forbid")

    column: optional_text(200) = None
    mobile_phase: optional_text(500) = None
    gradient: optional_text(1000) = None
    ionisation_mode: Literal["ESI+", "ESI-", "APCI+", "APCI-", "APPI+", "APPI-"] | None = None
    mass_analyser: optional_text(100) = None


def run_metadata_for(technique: str, data: dict | None) -> dict:
    """Validate run metadata for a technique; GC runs need the column polarity class for RI checks."""
    model = GCRun if technique in ("GC-MS", "GC-FID") else LCRun
    return model.model_validate(data or {}).model_dump(exclude_none=True)


class PreparationIn(BaseModel):
    batch_code: Code
    kind: Literal["extract", "essential_oil"]
    method_reference: constr(strip_whitespace=True, min_length=1, max_length=500)
    plant_material_mass_g: confloat(gt=0, allow_inf_nan=False) | None = None
    method_parameters: optional_text(1000) = None
    yield_percent: confloat(ge=0, le=100, allow_inf_nan=False) | None = None

    @model_validator(mode="after")
    def essential_oil_yield(self):
        if self.kind == "essential_oil" and self.yield_percent is None:
            raise ValueError("Report the essential-oil yield (% w/w).")
        return self


class CompoundCorrectionIn(BaseModel):
    model_config = ConfigDict(extra="forbid")

    cid: conint(gt=0, lt=2 ** 31) | None
    reason: constr(strip_whitespace=True, min_length=1, max_length=1000)


class PublicState(BaseModel):
    is_public: bool


