from typing import Annotated, Literal

from pydantic import AfterValidator, BaseModel, ConfigDict, Field, conlist, constr, field_validator


def unique_items(values):
    if len(set(values)) != len(values):
        raise ValueError("the list has duplicated items")
    return values



ShortText = constr(strip_whitespace=True, min_length=1, max_length=200)
Reason = constr(strip_whitespace=True, min_length=1, max_length=1000)
Identifier = constr(strip_whitespace=True, min_length=1, max_length=50)
Digest = constr(pattern=r"^[0-9a-f]{64}$")
InstitutionCode = constr(strip_whitespace=True, pattern=r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,39}$")
DOI = constr(strip_whitespace=True, max_length=200, pattern=r"^10\.[0-9]+/\S+$")
MAX_VOUCHERS = 200


class DepositionInput(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Contributor(DepositionInput):
    name: ShortText
    role: ShortText
    orcid: constr(strip_whitespace=True, pattern=r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$") | None = None

    @field_validator("orcid")
    @classmethod
    def valid_orcid_checksum(cls, value):
        if value is None:
            return value
        digits = value.replace("-", "")
        total = 0
        for digit in digits[:-1]:
            total = (total + int(digit)) * 2
        check = (12 - total % 11) % 11
        if digits[-1] != ("X" if check == 10 else str(check)):
            raise ValueError("Enter a valid ORCID iD, e.g. 0000-0002-1825-0097.")
        return value


class Draft(DepositionInput):
    # Kept so earlier drafts still load. Snapshots use the registered institution name.
    institution_name: ShortText | None = None
    title: ShortText | None = None
    description: constr(strip_whitespace=True, max_length=10000) = ""
    license: ShortText | None = None
    rights_statement: constr(strip_whitespace=True, max_length=2000) = ""
    contributors: conlist(Contributor, max_length=50) = Field(default_factory=list)
    profile_ids: Annotated[conlist(Identifier, max_length=50), AfterValidator(unique_items)] = Field(default_factory=list)
    specimen_ids: Annotated[conlist(Identifier, max_length=MAX_VOUCHERS), AfterValidator(unique_items)] = Field(
        default_factory=list)
    include_determiner_names: bool = False
    include_collector_names: bool = False
    correction_reason: Reason | None = None


def upper_code(value):
    return value.upper()


class CreateDeposition(Draft):
    institution: InstitutionCode

    @field_validator("institution")
    @classmethod
    def _normalize_institution(cls, value):
        return upper_code(value)


class EditDraft(Draft):
    expected_revision: Identifier | None = Field(...)


class PublishDraft(DepositionInput):
    draft_revision: Identifier
    snapshot_sha256: Digest


def lower_doi(value):
    return value.lower()


class ArticleLink(DepositionInput):
    doi: DOI

    @field_validator("doi")
    @classmethod
    def _normalize_doi(cls, value):
        return lower_doi(value)


class DatasetDOI(DepositionInput):
    doi: DOI
    agency: constr(strip_whitespace=True, pattern=r"^(datacite|zenodo|crossref|other)$")
    record_url: constr(strip_whitespace=True, max_length=500, pattern=r"^https://\S+$") | None = None

    @field_validator("doi")
    @classmethod
    def _normalize_doi(cls, value):
        return lower_doi(value)


class WithdrawVersion(DepositionInput):
    reason: Reason


class RegistrySource(DepositionInput):
    """A registry record the curator filled the form from; stored as provenance, never in snapshots."""
    provider: Literal["ror", "index_herbariorum"]
    external_id: constr(strip_whitespace=True, min_length=1, max_length=100)
    retrieved_at: constr(max_length=40) | None = None


class RegisterInstitution(DepositionInput):
    code: InstitutionCode
    name: ShortText
    index_herbariorum_code: constr(strip_whitespace=True, pattern=r"^[A-Za-z]{1,20}$") | None = None
    ror_id: constr(strip_whitespace=True, pattern=r"^(https://ror\.org/)?0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$") | None = None
    sources: conlist(RegistrySource, max_length=2) = []

    @field_validator("code")
    @classmethod
    def _normalize_code(cls, value):
        return upper_code(value)

    @field_validator("index_herbariorum_code")
    @classmethod
    def upper_herbarium_code(cls, value):
        return value.upper() if value else value

    @field_validator("ror_id")
    @classmethod
    def bare_ror_id(cls, value):
        return value.removeprefix("https://ror.org/") if value else value
