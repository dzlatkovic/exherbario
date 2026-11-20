"""Build the public projection a curator approves for one version."""

from hashlib import sha256
from urllib.parse import urlsplit

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.catalog import public_location
from app.chemistry.sample_links import PROVENANCE, determination_at_link, public_site, redetermined
from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.chemistry.repository import ChemistryRepository
from app.chemistry.services.chemistry_services import ChemistryService
from app.chemistry.services.profile_import import MAX_CSV_BYTES
from app.config import settings
from app.specimen.models import Specimen
from app.taxonomy.models import Taxonomy
from app.users.models import User

from .archive import MAX_VOUCHERS, SCHEMA_VERSION
from .models import Institution
from .schemas import Draft


def version_path(deposition, number):
    return f"/api/depositions/public/{deposition.institution}/{deposition.accession}/versions/{number}"


def landing_path(deposition, number):
    return f"/depositions/{deposition.institution}/{deposition.accession}/versions/{number}"


def public_base_url():
    """The configured public origin, required before a version can be previewed or published."""
    base = settings.PUBLIC_BASE_URL.strip().rstrip("/")
    parts = urlsplit(base)
    # A path is allowed for instances served under a prefix, e.g. https://example.edu/herbar.
    if parts.scheme not in {"http", "https"} or not parts.netloc or parts.query or parts.fragment:
        raise HTTPException(409, "Set PUBLIC_BASE_URL to this instance's public address, e.g. "
                                 "https://herbar.example.edu, before previewing or publishing.")
    return base


def version_url(deposition, number):
    """The absolute API URL of a version when the public origin is configured, else its path."""
    try:
        return public_base_url() + version_path(deposition, number)
    except HTTPException:
        return version_path(deposition, number)


def _voucher_metadata(voucher, taxon, draft):
    determination = {
        "name_as_recorded": voucher.subnomen,
        "date": voucher.determination_date,
        "taxonomy": {
            "id": taxon.taxon_id, "name": taxon.taxon_name, "rank": taxon.taxon_rank, "gbif_key": taxon.gbif_key,
            "authority": taxon.authority,
        } if taxon else None,
    }
    if draft.include_determiner_names:
        determination["determiner_name"] = voucher.determiner_name
    metadata = {
        "id": voucher.specimen_id, "reg_no": voucher.reg_no, "holding_type": voucher.holding_type,
        "holding_institution": voucher.holding_institution, "collection": voucher.collection,
        "accession": voucher.accession, "collector_number": voucher.collector_number,
        "type_status": voucher.type_status, "collection_date": voucher.collection_date,
        "verbatim_collection_date": voucher.verbatim_collection_date,
        "location": public_location(voucher, voucher.field_loc), "determination": determination,
    }
    if draft.include_collector_names:
        metadata["collector_name"] = voucher.collector_name
    return metadata


def selected_records(db, deposition, profile_ids):
    owner = db.get(User, deposition.owner_id)
    if owner is None or not owner.is_active:
        raise HTTPException(409, "The draft owner must have an active account.")
    if not profile_ids:
        return {}
    records = db.execute(
        select(Profile, Preparation, LabSample, Study)
        .join(Preparation, Profile.preparation_id == Preparation.id)
        .join(LabSample, Preparation.sample_id == LabSample.id)
        .join(Study, LabSample.study_id == Study.id)
        .where(Profile.id.in_(profile_ids))
    ).all()
    links = ChemistryRepository(db).list_sample_links(sorted({sample.id for _, _, sample, _ in records}))
    return {
        profile.id: (profile, preparation, sample, study, links[sample.id])
        for profile, preparation, sample, study in records
        if (owner.is_superuser or study.owner_id == owner.user_id)
    }


def _sample_metadata(sample, links):
    return {
        "id": sample.id, "code": sample.code, **{name: getattr(sample, name) for name in PROVENANCE},
        "site": public_site(sample, links),
        "vouchers": [{
            "id": link.specimen_id, "role": link.role, "determination_at_link": determination_at_link(link),
            "redetermined_since_linking": redetermined(link, voucher),
        } for link, voucher, _ in links],
    }


def selected_vouchers(db, specimen_ids):
    if not specimen_ids:
        return {}
    rows = db.execute(
        select(Specimen, Taxonomy)
        .outerjoin(Taxonomy, Specimen.taxon_id == Taxonomy.taxon_id)
        .where(Specimen.specimen_id.in_(specimen_ids))
    )
    return {voucher.specimen_id: (voucher, taxon) for voucher, taxon in rows}


def registered_institution(db, code):
    institution = db.get(Institution, code)
    if institution is None:
        raise HTTPException(409, f"Register institution code {code} with POST /api/institutions first.")
    return institution


def build_snapshot(db, deposition):
    draft = Draft.model_validate(deposition.draft)
    required = [name for name in ("title", "license", "contributors") if not getattr(draft, name)]
    if not (draft.profile_ids or draft.specimen_ids):
        required.append("profile_ids or specimen_ids")
    if required:
        raise HTTPException(409, "Complete the draft fields: " + ", ".join(required))
    base = public_base_url()
    institution = registered_institution(db, deposition.institution)
    records = selected_records(db, deposition, draft.profile_ids)
    if set(records) != set(draft.profile_ids) or any(
        not (profile.is_public and study.is_public and links and all(voucher.is_public for _, voucher, _ in links))
        for profile, _, _, study, links in records.values()
    ):
        raise HTTPException(409, "Select released profiles from studies available to the draft owner, "
                                 "with every linked voucher released.")
    listed = selected_vouchers(db, draft.specimen_ids)
    if set(listed) != set(draft.specimen_ids) or not all(voucher.is_public for voucher, _ in listed.values()):
        raise HTTPException(409, "Select vouchers that exist and have been released by a curator.")
    linked_ids = [link.specimen_id for *_, links in records.values() for link, _, _ in links]
    linked = selected_vouchers(db, [specimen_id for specimen_id in linked_ids if specimen_id not in listed])
    measurements = {profile_id: [] for profile_id in draft.profile_ids}
    if draft.profile_ids:
        for row in ChemistryRepository(db).list_measurements(draft.profile_ids):
            measurements[row.profile_id].append({
                "feature": row.feature, "value": row.value, "confidence": row.confidence, "status": row.status,
            })
    if len(set(draft.specimen_ids) | set(linked_ids)) > MAX_VOUCHERS:
        raise HTTPException(409, f"A deposition version can list at most {MAX_VOUCHERS} vouchers.")
    if not all(measurements.values()):
        raise HTTPException(409, "Each selected profile must have recorded measurements.")
    number = deposition.latest_version + 1
    url = base + version_path(deposition, number)
    vouchers = {specimen_id: listed[specimen_id] for specimen_id in draft.specimen_ids}
    profiles, files = [], {}
    for profile_id in draft.profile_ids:
        profile, preparation, sample, study, links = records[profile_id]
        for link, _, _ in links:
            vouchers.setdefault(link.specimen_id, linked.get(link.specimen_id) or listed[link.specimen_id])
        content = ChemistryService.read_profile_source(profile)
        if not content or len(content) > MAX_CSV_BYTES:
            raise HTTPException(409, f"Profile {profile_id} has an empty or oversized source file.")
        files[profile_id] = content
        profiles.append({
            "id": profile_id, "run_code": profile.run_code, "analytical_method": profile.analytical_method,
            "measurement_basis": profile.measurement_basis, "unit": profile.unit,
            "measurements": measurements[profile_id],
            "study": {"id": study.id, "title": study.title},
            "sample": _sample_metadata(sample, links),
            "preparation": {"id": preparation.id, "batch_code": preparation.batch_code, "kind": preparation.kind,
                            "method_reference": preparation.method_reference},
            "file": {"name": profile.source_name, "source_fidelity": profile.source_fidelity,
                     "sha256": sha256(content).hexdigest(), "size": len(content), "url": f"{url}/files/{profile_id}"},
        })
    snapshot = jsonable_encoder({
        "schema_version": SCHEMA_VERSION, "institution": deposition.institution,
        "institution_name": institution.name,
        "institution_identifiers": {
            "index_herbariorum": institution.index_herbariorum_code,
            "ror": f"https://ror.org/{institution.ror_id}" if institution.ror_id else None,
        },
        "accession": deposition.accession, "version": number,
        "identifier": base + landing_path(deposition, number), "url": url,
        "supersedes": base + version_path(deposition, number - 1) if number > 1 else None,
        "title": draft.title, "description": draft.description, "license": draft.license,
        "rights_statement": draft.rights_statement,
        "contributors": [contributor.model_dump(exclude_none=True) for contributor in draft.contributors],
        "correction_reason": draft.correction_reason,
        "vouchers": [_voucher_metadata(voucher, taxon, draft) for voucher, taxon in vouchers.values()],
        "profiles": profiles,
    })
    return snapshot, files
