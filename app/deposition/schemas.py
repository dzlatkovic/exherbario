from pydantic import BaseModel, Field, conlist, constr, validator


ShortText = constr(strip_whitespace=True, min_length=1, max_length=200)
Reason = constr(strip_whitespace=True, min_length=1, max_length=1000)
Identifier = constr(strip_whitespace=True, min_length=1, max_length=50)
Digest = constr(regex=r"^[0-9a-f]{64}$")


class DepositionInput(BaseModel):
    class Config:
        extra = "forbid"


class Contributor(DepositionInput):
    name: ShortText
    role: ShortText


class Draft(DepositionInput):
    institution_name: ShortText | None = None
    title: ShortText | None = None
    description: constr(strip_whitespace=True, max_length=10000) = ""
    license: ShortText | None = None
    rights_statement: constr(strip_whitespace=True, max_length=2000) = ""
    contributors: conlist(Contributor, max_items=50) = Field(default_factory=list)
    profile_ids: conlist(Identifier, max_items=50, unique_items=True) = Field(default_factory=list)
    include_determiner_names: bool = False
    correction_reason: Reason | None = None


class CreateDeposition(Draft):
    institution: constr(strip_whitespace=True, regex=r"^[a-zA-Z0-9][a-zA-Z0-9-]{0,39}$")

    @validator("institution")
    def normalize_institution(cls, value):
        return value.upper()


class EditDraft(Draft):
    expected_revision: Identifier | None = Field(...)


class PublishDraft(DepositionInput):
    draft_revision: Identifier
    snapshot_sha256: Digest


class ArticleLink(DepositionInput):
    doi: constr(strip_whitespace=True, max_length=200, regex=r"^10\.[0-9]+/\S+$")

    @validator("doi")
    def normalize_doi(cls, value):
        return value.lower()


class WithdrawVersion(DepositionInput):
    reason: Reason
