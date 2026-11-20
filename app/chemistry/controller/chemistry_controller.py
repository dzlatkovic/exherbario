"""HTTP responses and serialization for the chemistry API."""

import json

from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, Preparation, Profile, Study
from app.chemistry.sample_links import (PROVENANCE, current_determination, determination_at_link, public_site,
                                        redetermined)
from app.chemistry.schemas import (Basis, CompoundCorrectionIn, PreparationIn, PublicState, SampleIn, StudyIn,
                                   Technique, VoucherLinkIn)
from app.chemistry.services import ChemistryService
from app.chemistry.records import correction_record, measurement_record, preparation_summary
from app.chemistry.services.compounds import candidate_summary, compound_summary
from app.users.models import User


async def chemistry_error_response(_request: Request, error: ChemistryError):
    return JSONResponse(status_code=error.code, content={"detail": str(error)})


def _study_summary(study: Study):
    return {
        "id": study.id, "title": study.title, "description": study.description,
        "publication_id": study.publication_id, "is_public": study.is_public,
    }


def _profile_summary(profile: Profile):
    return {
        "id": profile.id, "preparation_id": profile.preparation_id, "run_code": profile.run_code,
        "analytical_method": profile.analytical_method, "measurement_basis": profile.measurement_basis,
        "unit": profile.unit, "source_name": profile.source_name, "is_public": profile.is_public,
        "source_fidelity": profile.source_fidelity, "source_sha256": profile.source_sha256,
        "technique": profile.technique, "run_metadata": profile.run_metadata,
        "import_id": profile.import_id, "import_column": profile.import_column,
    }


def _workspace_link(link, specimen, taxon_name):
    return {
        "specimen_id": link.specimen_id, "role": link.role, "reg_no": specimen.reg_no,
        "holding_institution": specimen.holding_institution, "collection": specimen.collection,
        "accession": specimen.accession, "is_public": bool(specimen.is_public),
        "determination_at_link": determination_at_link(link),
        "current_determination": current_determination(specimen, taxon_name),
        "redetermined": redetermined(link, specimen),
    }


def _public_link(link, specimen, _taxon_name):
    return {
        "specimen_id": link.specimen_id, "role": link.role,
        "determination_at_link": determination_at_link(link), "redetermined": redetermined(link, specimen),
    }


def _workspace_sample(sample: LabSample, links):
    return {
        "id": sample.id, "code": sample.code, **{name: getattr(sample, name) for name in PROVENANCE},
        "site_specimen_id": sample.site_specimen_id, "field_loc_id": sample.field_loc_id,
        "collection_notes": sample.collection_notes,
        "vouchers": [_workspace_link(*row) for row in links],
        "redetermined": any(redetermined(link, specimen) for link, specimen, _ in links),
    }


def _released_profile_summary(profile: Profile, preparation: Preparation, sample: LabSample, links):
    return {
        "id": profile.id, "study_id": sample.study_id, "sample_code": sample.code,
        **{name: getattr(sample, name) for name in PROVENANCE}, "site": public_site(sample, links),
        "vouchers": [_public_link(*row) for row in links],
        "redetermined": any(redetermined(link, specimen) for link, specimen, _ in links),
        "batch_code": preparation.batch_code, "preparation_kind": preparation.kind,
        "method_reference": preparation.method_reference,
        "plant_material_mass_g": preparation.plant_material_mass_g,
        "method_parameters": preparation.method_parameters, "yield_percent": preparation.yield_percent,
        "run_code": profile.run_code, "analytical_method": profile.analytical_method,
        "measurement_basis": profile.measurement_basis, "unit": profile.unit,
        "technique": profile.technique, "run_metadata": profile.run_metadata,
    }


def _measurements(rows):
    return [measurement_record(row, compound) for row, compound in rows]


class ChemistryController:
    def __init__(self, service: ChemistryService):
        self.service = service

    def list_studies(self, actor: User):
        studies = self.service.list_studies(actor)
        return {"can_publish": actor.is_superuser, "studies": [_study_summary(study) for study in studies]}

    def create_study(self, data: StudyIn, actor: User):
        return _study_summary(self.service.create_study(data, actor))

    def get_study(self, study_id: str, actor: User):
        study, samples, links, preparations, profiles = self.service.get_study(study_id, actor)
        redetermined_samples = {
            sample_id for sample_id, rows in links.items()
            if any(redetermined(link, specimen) for link, specimen, _ in rows)
        }
        return {
            **_study_summary(study),
            "samples": [_workspace_sample(sample, links[sample.id]) for sample in samples],
            "preparations": [preparation_summary(preparation) for preparation in preparations],
            "profiles": [
                {**_profile_summary(profile), "sample_code": sample.code, "batch_code": preparation.batch_code,
                 "redetermined": sample.id in redetermined_samples}
                for profile, preparation, sample in profiles
            ],
        }

    def create_sample(self, study_id: str, data: SampleIn, actor: User):
        return {"id": self.service.create_sample(study_id, data, actor).id}

    def add_sample_voucher(self, sample_id: str, data: VoucherLinkIn, actor: User):
        link = self.service.add_sample_voucher(sample_id, data, actor)
        return {"sample_id": link.sample_id, "specimen_id": link.specimen_id, "role": link.role,
                "determination_at_link": determination_at_link(link)}

    def remove_sample_voucher(self, sample_id: str, specimen_id: str, actor: User):
        self.service.remove_sample_voucher(sample_id, specimen_id, actor)

    def create_preparation(self, sample_id: str, data: PreparationIn, actor: User):
        return {"id": self.service.create_preparation(sample_id, data, actor).id}

    def import_profile(self, preparation_id: str, file: UploadFile, run_code: str,
                       analytical_method: str, measurement_basis: Basis, unit: str, actor: User,
                       technique: Technique, run_metadata: str):
        try:
            run = json.loads(run_metadata or "{}")
        except ValueError as error:
            raise ChemistryError(422, "Send run_metadata as a JSON object.") from error
        if not isinstance(run, dict):
            raise ChemistryError(422, "Send run_metadata as a JSON object.")
        profile, warnings = self.service.import_profile(
            preparation_id, file.file, file.filename, run_code, analytical_method,
            measurement_basis, unit, actor, technique, run,
        )
        return {**_profile_summary(profile), "warnings": warnings}

    def get_profile(self, profile_id: str, actor: User):
        profile, rows, corrections = self.service.get_profile(profile_id, actor)
        return {**_profile_summary(profile), "measurements": _measurements(rows),
                "compound_corrections": [correction_record(item) for item in corrections]}

    def correct_compound(self, profile_id: str, feature: str, data: CompoundCorrectionIn, actor: User):
        return correction_record(self.service.correct_compound(profile_id, feature, data, actor))

    def search_compounds(self, query: str, namespace: str):
        return [candidate_summary(record) for record in self.service.registry.search(query, namespace)]

    def parent_compound(self, cid: int):
        return candidate_summary(self.service.registry.parent(cid))

    def get_public_compound(self, cid: int):
        compound = self.service.repository.get_compound(cid)
        if compound is None:
            raise ChemistryError(404, "Compound not registered.")
        return compound_summary(compound)

    def download_source(self, profile_id: str, actor: User):
        source, profile = self.service.get_profile_source(profile_id, actor)
        headers = {
            "Content-Disposition": 'attachment; filename="profile-source.csv"',
            "Cache-Control": "no-store",
            "X-Content-Type-Options": "nosniff",
            "X-HERBAR-Source-Fidelity": profile.source_fidelity,
        }
        if profile.source_sha256 is not None:
            headers["X-HERBAR-SHA256"] = profile.source_sha256
        return Response(source, media_type="text/csv", headers=headers)

    def set_study_visibility(self, study_id: str, data: PublicState, actor: User):
        return _study_summary(self.service.set_study_visibility(study_id, data.is_public, actor))

    def set_profile_visibility(self, profile_id: str, data: PublicState, actor: User):
        return _profile_summary(self.service.set_profile_visibility(profile_id, data.is_public, actor))

    def get_public_study(self, study_id: str):
        study, profiles, links = self.service.get_public_study(study_id)
        return {
            **_study_summary(study),
            "profiles": [_released_profile_summary(*record, links[record[2].id]) for record in profiles],
        }

    def get_public_profile(self, profile_id: str):
        record, links, rows, corrections = self.service.get_public_profile(profile_id)
        return {**_released_profile_summary(*record, links[record[2].id]), "measurements": _measurements(rows),
                "compound_corrections": [correction_record(item) for item in corrections]}

    def get_public_specimen_profiles(self, specimen_id: str):
        profiles, links = self.service.get_public_specimen_profiles(specimen_id)
        return [_released_profile_summary(*record, links[record[2].id]) for record in profiles]
