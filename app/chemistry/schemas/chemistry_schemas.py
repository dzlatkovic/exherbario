from typing import Literal

from pydantic import BaseModel, Field, constr

Code = constr(strip_whitespace=True, min_length=1, max_length=80)
Basis = Literal["concentration", "peak_area", "peak_area_percent"]


class StudyIn(BaseModel):
    title: constr(strip_whitespace=True, min_length=1, max_length=200)
    description: constr(strip_whitespace=True, max_length=4000) = ""
    publication_id: str | None = Field(None, max_length=50)


class SampleIn(BaseModel):
    specimen_id: str = Field(min_length=1, max_length=50)
    code: Code
    plant_part: constr(strip_whitespace=True, min_length=1, max_length=100)
    collection_event: constr(strip_whitespace=True, min_length=1, max_length=200)
    voucher_relationship: Literal["sampled_from_voucher", "collected_alongside"]


class PreparationIn(BaseModel):
    batch_code: Code
    kind: Literal["extract", "essential_oil"]
    method_reference: constr(strip_whitespace=True, min_length=1, max_length=500)


class PublicState(BaseModel):
    is_public: bool


class PCAIn(BaseModel):
    profile_ids: list[str] = Field(min_items=3, max_items=50)
    scale: bool = True
