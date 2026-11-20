"""HTTP responses and serialization for the chemistry API."""

from fastapi import Request, UploadFile
from fastapi.responses import JSONResponse, Response

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, Measurement, PCAAnalysis, Preparation, Profile, Study
from app.chemistry.schemas import Basis, PCAIn, PreparationIn, PublicState, SampleIn, StudyIn
from app.chemistry.services import ChemistryService
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
    }


def _released_profile_summary(profile: Profile, preparation: Preparation, sample: LabSample):
    return {
        "id": profile.id, "study_id": sample.study_id, "specimen_id": sample.specimen_id,
        "sample_code": sample.code, "plant_part": sample.plant_part,
        "voucher_relationship": sample.voucher_relationship,
        "batch_code": preparation.batch_code, "preparation_kind": preparation.kind,
        "method_reference": preparation.method_reference, "run_code": profile.run_code,
        "analytical_method": profile.analytical_method, "measurement_basis": profile.measurement_basis,
        "unit": profile.unit,
    }


def _measurements(rows: list[Measurement]):
    return [
        {"feature": row.feature, "value": row.value, "confidence": row.confidence, "status": row.status}
        for row in rows
    ]


def _analysis_summary(analysis: PCAAnalysis):
    return {
        "id": analysis.id, "created_at": analysis.created_at,
        "profile_ids": analysis.profile_ids, "configuration": analysis.configuration,
        **analysis.results,
    }


class ChemistryController:
    def __init__(self, service: ChemistryService):
        self.service = service

    def list_studies(self, actor: User):
        studies = self.service.list_studies(actor)
        return {"can_publish": actor.is_superuser, "studies": [_study_summary(study) for study in studies]}

    def create_study(self, data: StudyIn, actor: User):
        return _study_summary(self.service.create_study(data, actor))

    def get_study(self, study_id: str, actor: User):
        study, samples, preparations, profiles, analyses = self.service.get_study(study_id, actor)
        return {
            **_study_summary(study),
            "samples": [
                {"id": sample.id, "code": sample.code, "specimen_id": sample.specimen_id,
                 "reg_no": reg_no, "plant_part": sample.plant_part,
                 "collection_event": sample.collection_event,
                 "voucher_relationship": sample.voucher_relationship}
                for sample, reg_no in samples
            ],
            "preparations": [
                {"id": preparation.id, "sample_id": preparation.sample_id,
                 "batch_code": preparation.batch_code, "kind": preparation.kind,
                 "method_reference": preparation.method_reference}
                for preparation in preparations
            ],
            "profiles": [
                {**_profile_summary(profile), "sample_code": sample.code, "batch_code": preparation.batch_code}
                for profile, preparation, sample in profiles
            ],
            "analyses": [{"id": analysis_id, "created_at": created_at} for analysis_id, created_at in analyses],
        }

    def create_sample(self, study_id: str, data: SampleIn, actor: User):
        return {"id": self.service.create_sample(study_id, data, actor).id}

    def create_preparation(self, sample_id: str, data: PreparationIn, actor: User):
        return {"id": self.service.create_preparation(sample_id, data, actor).id}

    def import_profile(self, preparation_id: str, file: UploadFile, run_code: str,
                       analytical_method: str, measurement_basis: Basis, unit: str, actor: User):
        profile = self.service.import_profile(
            preparation_id, file.file, file.filename, run_code, analytical_method,
            measurement_basis, unit, actor,
        )
        return _profile_summary(profile)

    def get_profile(self, profile_id: str, actor: User):
        profile, rows = self.service.get_profile(profile_id, actor)
        return {**_profile_summary(profile), "measurements": _measurements(rows)}

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

    def run_pca(self, study_id: str, data: PCAIn, actor: User):
        return _analysis_summary(self.service.run_pca(study_id, data, actor))

    def get_pca(self, study_id: str, analysis_id: str, actor: User):
        return _analysis_summary(self.service.get_pca(study_id, analysis_id, actor))

    def get_public_study(self, study_id: str):
        study, profiles = self.service.get_public_study(study_id)
        return {
            **_study_summary(study),
            "profiles": [_released_profile_summary(*record) for record in profiles],
        }

    def get_public_profile(self, profile_id: str):
        record, rows = self.service.get_public_profile(profile_id)
        return {**_released_profile_summary(*record), "measurements": _measurements(rows)}

    def get_public_specimen_profiles(self, specimen_id: str):
        profiles = self.service.get_public_specimen_profiles(specimen_id)
        return [_released_profile_summary(*record) for record in profiles]
