from pydantic import BaseModel, Field, conlist, constr, validator


ShortText = constr(strip_whitespace=True, min_length=1, max_length=200)
Reason = constr(strip_whitespace=True, min_length=1, max_length=1000)
Identifier = constr(strip_whitespace=True, min_length=1, max_length=50)
Digest = constr(regex=r"^[0-9a-f]{64}$")
InstitutionCode = constr(strip_whitespace=True, regex=r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,39}$")
DOI = constr(strip_whitespace=True, max_length=200, regex=r"^10\.[0-9]+/\S+$")
MAX_VOUCHERS = 200


class DepositionInput(BaseModel):
    class Config:
        extra = "forbid"


class Contributor(DepositionInput):
    name: ShortText
    role: ShortText
    orcid: constr(strip_whitespace=True, regex=r"^\d{4}-\d{4}-\d{4}-\d{3}[\dX]$") | None = None

    @validator("orcid")
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
    contributors: conlist(Contributor, max_items=50) = Field(default_factory=list)
    profile_ids: conlist(Identifier, max_items=50, unique_items=True) = Field(default_factory=list)
    specimen_ids: conlist(Identifier, max_items=MAX_VOUCHERS, unique_items=True) = Field(default_factory=list)
    include_determiner_names: bool = False
    include_collector_names: bool = False
    correction_reason: Reason | None = None


def upper_code(value):
    return value.upper()


class CreateDeposition(Draft):
    institution: InstitutionCode

    _normalize_institution = validator("institution", allow_reuse=True)(upper_code)


class EditDraft(Draft):
    expected_revision: Identifier | None = Field(...)


class PublishDraft(DepositionInput):
    draft_revision: Identifier
    snapshot_sha256: Digest


def lower_doi(value):
    return value.lower()


class ArticleLink(DepositionInput):
    doi: DOI

    _normalize_doi = validator("doi", allow_reuse=True)(lower_doi)


class DatasetDOI(DepositionInput):
    doi: DOI
    agency: constr(strip_whitespace=True, regex=r"^(datacite|zenodo|crossref|other)$")
    record_url: constr(strip_whitespace=True, max_length=500, regex=r"^https://\S+$") | None = None

    _normalize_doi = validator("doi", allow_reuse=True)(lower_doi)


class WithdrawVersion(DepositionInput):
    reason: Reason


class RegisterInstitution(DepositionInput):
    code: InstitutionCode
    name: ShortText
    index_herbariorum_code: constr(strip_whitespace=True, regex=r"^[A-Za-z]{1,20}$") | None = None
    ror_id: constr(strip_whitespace=True, regex=r"^(https://ror\.org/)?0[a-hj-km-np-tv-z0-9]{6}[0-9]{2}$") | None = None

    _normalize_code = validator("code", allow_reuse=True)(upper_code)

    @validator("index_herbariorum_code")
    def upper_herbarium_code(cls, value):
        return value.upper() if value else value

    @validator("ror_id")
    def bare_ror_id(cls, value):
        return value.removeprefix("https://ror.org/") if value else value
