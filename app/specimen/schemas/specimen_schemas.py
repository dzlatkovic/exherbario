"""This module contains Pydantic models for working with specimen data."""


from datetime import date
from typing import Literal, Optional

from pydantic import BaseModel, Field, UUID4, constr, root_validator


PersonName = constr(strip_whitespace=True, min_length=1, max_length=200)
CollectionName = constr(strip_whitespace=True, min_length=1, max_length=120)
Accession = constr(strip_whitespace=True, min_length=1, max_length=100)
RegistrationNumber = constr(strip_whitespace=True, min_length=1, max_length=10)


class VoucherMetadata(BaseModel):
    holding_type: Literal["local", "external"] | None = None
    holding_institution: CollectionName | None = None
    collection: CollectionName | None = None
    accession: Accession | None = None
    verbatim_label: constr(max_length=10000) | None = None
    collector_name: PersonName | None = None
    verifier_name: PersonName | None = None
    determiner_name: PersonName | None = None
    determination_date: date | None = None


class SpecimenSchema(VoucherMetadata):
    """An archive record can have unknown scientific values."""
    specimen_id: UUID4
    reg_no: str | None
    collection_date: date | None
    reg_date: date | None
    taxon_id: str | None
    subnomen: str | None
    field_loc_id: str | None
    storage_id: str | None
    collected_by: str | None
    verified_by: str | None

    class Config:
        orm_mode = True


class SpecimenSchemaIn(VoucherMetadata):
    """Register a single voucher with any scientific information available."""
    reg_no: RegistrationNumber | None = None
    collection_date: date | None = None
    reg_date: date = Field(default_factory=date.today)
    taxon_id: str | None = None
    subnomen: constr(max_length=200) | None = None
    field_loc_id: str | None = None
    storage_id: str | None = None
    collected_by: str | None = None
    verified_by: str | None = None

    @root_validator(skip_on_failure=True)
    def holding_or_legacy_number(cls, values):
        if not values.get("holding_type") and not values.get("reg_no"):
            raise ValueError("Choose local or external holding, or supply a legacy registration number.")
        return values


class SpecimenSchemaUpdate(VoucherMetadata):
    """Pydantic model for updating a specimen record."""
    reg_no: Optional[str]
    collection_date: Optional[date]
    taxon_id: Optional[str]
    subnomen: Optional[str]
    field_loc_id: Optional[str]
    storage_id: Optional[str]
    collected_by: Optional[str]
    verified_by: Optional[str]
    correction_reason: Optional[constr(strip_whitespace=True, min_length=1, max_length=1000)] = None
