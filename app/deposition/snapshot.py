"""Build the public projection a curator approves for one version."""

import json
from hashlib import sha256

from fastapi import HTTPException
from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.catalog import public_location
from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.chemistry.repository import ChemistryRepository
from app.chemistry.services.chemistry_services import ChemistryService
from app.chemistry.services.profile_import import MAX_CSV_BYTES
from app.specimen.models import Specimen
from app.taxonomy.models import Taxonomy
from app.users.models import User

from .schemas import Draft


def snapshot_digest(snapshot):
    encoded = json.dumps(snapshot, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False)
    return sha256(encoded.encode("utf-8")).hexdigest()


def version_url(deposition, number):
    return f"/api/depositions/public/{deposition.institution}/{deposition.accession}/versions/{number}"


def _voucher_metadata(voucher, taxon, include_determiner):
    determination = {
        "name_as_recorded": voucher.subnomen,
        "date": voucher.determination_date,
        "taxonomy": {
            "id": taxon.taxon_id, "name": taxon.taxon_name, "rank": taxon.taxon_rank, "gbif_key": taxon.gbif_key,
        } if taxon else None,
    }
    if include_determiner:
        determination["determiner_name"] = voucher.determiner_name
    return {
        "id": voucher.specimen_id, "reg_no": voucher.reg_no, "holding_type": voucher.holding_type,
        "holding_institution": voucher.holding_institution, "collection": voucher.collection,
        "accession": voucher.accession, "collection_date": voucher.collection_date,
        "location": public_location(voucher, voucher.field_loc), "determination": determination,
    }


def build_snapshot(db, deposition):
    draft = Draft.parse_obj(deposition.draft)
    required = [name for name in ("institution_name", "title", "license", "contributors", "profile_ids")
                if not getattr(draft, name)]
    if required:
        raise HTTPException(409, "Complete the draft fields: " + ", ".join(required))
    owner = db.get(User, deposition.owner_id)
    if owner is None or not owner.is_active:
        raise HTTPException(409, "The draft owner must have an active account.")
    records = db.execute(
        select(Profile, Preparation, LabSample, Study, Specimen, Taxonomy)
        .join(Preparation, Profile.preparation_id == Preparation.id)
        .join(LabSample, Preparation.sample_id == LabSample.id)
        .join(Study, LabSample.study_id == Study.id)
        .join(Specimen, LabSample.specimen_id == Specimen.specimen_id)
        .outerjoin(Taxonomy, Specimen.taxon_id == Taxonomy.taxon_id)
        .where(Profile.id.in_(draft.profile_ids))
    )
    eligible = {
        profile.id: (profile, preparation, sample, study, voucher, taxon)
        for profile, preparation, sample, study, voucher, taxon in records
        if (owner.is_superuser or study.owner_id == owner.user_id)
        and profile.is_public and study.is_public and voucher.is_public
    }
    if set(eligible) != set(draft.profile_ids):
        raise HTTPException(409, "Select released profiles from studies available to the draft owner and released vouchers.")
    measurements = {profile_id: [] for profile_id in draft.profile_ids}
    for row in ChemistryRepository(db).list_measurements(draft.profile_ids):
        measurements[row.profile_id].append({
            "feature": row.feature, "value": row.value, "confidence": row.confidence, "status": row.status,
        })
    if not all(measurements.values()):
        raise HTTPException(409, "Each selected profile must have recorded measurements.")
    number = deposition.latest_version + 1
    url = version_url(deposition, number)
    profiles, files = [], {}
    for profile_id in draft.profile_ids:
        profile, preparation, sample, study, voucher, taxon = eligible[profile_id]
        content = ChemistryService.read_profile_source(profile)
        if not content or len(content) > MAX_CSV_BYTES:
            raise HTTPException(409, f"Profile {profile_id} has an empty or oversized source file.")
        files[profile_id] = content
        profiles.append({
            "id": profile_id, "run_code": profile.run_code, "analytical_method": profile.analytical_method,
            "measurement_basis": profile.measurement_basis, "unit": profile.unit,
            "measurements": measurements[profile_id],
            "study": {"id": study.id, "title": study.title},
            "sample": {"id": sample.id, "code": sample.code, "plant_part": sample.plant_part,
                       "voucher_relationship": sample.voucher_relationship},
            "preparation": {"id": preparation.id, "batch_code": preparation.batch_code, "kind": preparation.kind,
                            "method_reference": preparation.method_reference},
            "voucher": _voucher_metadata(voucher, taxon, draft.include_determiner_names),
            "file": {"name": profile.source_name, "source_fidelity": profile.source_fidelity,
                     "sha256": sha256(content).hexdigest(), "size": len(content), "url": f"{url}/files/{profile_id}"},
        })
    snapshot = jsonable_encoder({
        "schema_version": 1, "institution": deposition.institution, "institution_name": draft.institution_name,
        "accession": deposition.accession, "version": number, "url": url,
        "supersedes": version_url(deposition, number - 1) if number > 1 else None,
        "title": draft.title, "description": draft.description, "license": draft.license,
        "rights_statement": draft.rights_statement, "contributors": draft.contributors,
        "correction_reason": draft.correction_reason, "profiles": profiles,
    })
    return snapshot, files
