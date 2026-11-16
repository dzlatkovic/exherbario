"""Study access, profile import, and analysis workflows."""

from pathlib import PurePosixPath
from typing import BinaryIO

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, PCAAnalysis, Preparation, Profile, Study
from app.chemistry.repository import ChemistryRepository
from app.chemistry.schemas import Basis, PCAIn, PreparationIn, SampleIn, StudyIn
from app.users.models import User

from .pca_analysis import calculate_pca
from .profile_import import MAX_CSV_BYTES, read_measurements


class ChemistryService:
    def __init__(self, repository: ChemistryRepository):
        self.repository = repository

    def _study_for_actor(self, study_id: str, actor: User):
        study = self.repository.get_study(study_id)
        if not study or (not actor.is_superuser and study.owner_id != actor.user_id):
            raise ChemistryError(404, "Study not found.")
        return study

    def _profile_for_actor(self, profile_id: str, actor: User):
        profile = self.repository.get_profile(profile_id)
        if profile is None:
            raise ChemistryError(404, "Profile not found.")
        study_id = self.repository.get_preparation_study_id(profile.preparation_id)
        self._study_for_actor(study_id, actor)
        return profile

    def list_studies(self, actor: User):
        owner_id = None if actor.is_superuser else actor.user_id
        return self.repository.list_studies(owner_id)

    def create_study(self, data: StudyIn, actor: User):
        if data.publication_id and not self.repository.publication_exists(data.publication_id):
            raise ChemistryError(404, "Publication not found.")
        study = Study(owner_id=actor.user_id, **data.dict())
        self.repository.save(study)
        return study

    def get_study(self, study_id: str, actor: User):
        study = self._study_for_actor(study_id, actor)
        return (
            study,
            self.repository.list_study_samples(study_id),
            self.repository.list_study_preparations(study_id),
            self.repository.list_study_profiles(study_id),
            self.repository.list_study_analyses(study_id),
        )

    def create_sample(self, study_id: str, data: SampleIn, actor: User):
        self._study_for_actor(study_id, actor)
        if not self.repository.specimen_exists(data.specimen_id):
            raise ChemistryError(404, "Voucher specimen not found.")
        sample = LabSample(study_id=study_id, **data.dict())
        self.repository.save(sample)
        return sample

    def create_preparation(self, sample_id: str, data: PreparationIn, actor: User):
        sample = self.repository.get_sample(sample_id)
        if not sample:
            raise ChemistryError(404, "Sample not found.")
        self._study_for_actor(sample.study_id, actor)
        preparation = Preparation(sample_id=sample_id, **data.dict())
        self.repository.save(preparation)
        return preparation

    def import_profile(self, preparation_id: str, source_file: BinaryIO, source_name: str | None,
                       run_code: str, analytical_method: str, measurement_basis: Basis,
                       unit: str, actor: User):
        preparation = self.repository.get_preparation(preparation_id)
        if not preparation:
            raise ChemistryError(404, "Preparation not found.")
        sample = self.repository.get_sample(preparation.sample_id)
        self._study_for_actor(sample.study_id, actor)
        run_code, analytical_method, unit = (value.strip() for value in (run_code, analytical_method, unit))
        if not all((run_code, analytical_method, unit)):
            raise ChemistryError(422, "Enter a run code, analytical method, and unit.")
        if measurement_basis == "peak_area_percent" and unit != "%":
            raise ChemistryError(422, "Use % as the unit for normalized peak-area percentages.")
        content = source_file.read(MAX_CSV_BYTES + 1)
        try:
            source, rows = read_measurements(content, measurement_basis)
        except ValueError as error:
            raise ChemistryError(422, str(error)) from error
        filename = PurePosixPath((source_name or "profile.csv").replace("\\", "/")).name
        profile = Profile(preparation_id=preparation_id, run_code=run_code,
                          analytical_method=analytical_method, measurement_basis=measurement_basis,
                          unit=unit, source_name=filename[:200] or "profile.csv", source_csv=source)
        self.repository.save_profile(profile, rows)
        return profile

    def get_profile(self, profile_id: str, actor: User):
        profile = self._profile_for_actor(profile_id, actor)
        return profile, self.repository.list_measurements([profile_id])

    def get_profile_source(self, profile_id: str, actor: User) -> str:
        return self._profile_for_actor(profile_id, actor).source_csv

    def set_study_visibility(self, study_id: str, is_public: bool, actor: User):
        study = self._study_for_actor(study_id, actor)
        study.is_public = is_public
        self.repository.save(study)
        return study

    def set_profile_visibility(self, profile_id: str, is_public: bool, actor: User):
        profile = self._profile_for_actor(profile_id, actor)
        profile.is_public = is_public
        self.repository.save(profile)
        return profile

    def run_pca(self, study_id: str, data: PCAIn, actor: User):
        self._study_for_actor(study_id, actor)
        rows = self.repository.list_study_profiles(study_id, data.profile_ids)
        if len(rows) != len(data.profile_ids):
            raise ChemistryError(422, "Select distinct profiles from the current study.")
        indexed = {profile.id: (profile, preparation, sample) for profile, preparation, sample in rows}
        rows = [indexed[profile_id] for profile_id in data.profile_ids]
        if len({sample.id for _, _, sample in rows}) != len(rows):
            raise ChemistryError(422, "Select one profile per lab sample to avoid counting technical replicates twice.")
        methods = {
            (profile.analytical_method.casefold(), profile.measurement_basis, profile.unit,
             preparation.kind, preparation.method_reference.casefold())
            for profile, preparation, _ in rows
        }
        if len(methods) != 1:
            raise ChemistryError(422, "Select profiles with matching analytical method, units, and preparation method.")

        matrix = {profile_id: {} for profile_id in data.profile_ids}
        for measurement in self.repository.list_measurements(data.profile_ids):
            matrix[measurement.profile_id][measurement.feature.casefold()] = (
                measurement.feature, measurement.value
            )
        try:
            result = calculate_pca(
                [matrix[profile_id] for profile_id in data.profile_ids],
                basis=rows[0][0].measurement_basis, scale=data.scale,
            )
        except ValueError as error:
            raise ChemistryError(422, str(error)) from error
        configuration = result.pop("configuration")
        result["sample_codes"] = [sample.code for _, _, sample in rows]
        analysis = PCAAnalysis(study_id=study_id, created_by=actor.user_id, profile_ids=data.profile_ids,
                               configuration=configuration, results=result)
        self.repository.save(analysis)
        return analysis

    def get_pca(self, study_id: str, analysis_id: str, actor: User):
        self._study_for_actor(study_id, actor)
        analysis = self.repository.get_analysis(study_id, analysis_id)
        if analysis is None:
            raise ChemistryError(404, "Analysis not found.")
        return analysis

    def get_public_study(self, study_id: str):
        study = self.repository.get_study(study_id)
        if not study or not study.is_public:
            raise ChemistryError(404, "Study not found.")
        return study, self.repository.list_released_study_profiles(study_id)

    def get_public_profile(self, profile_id: str):
        record = self.repository.get_released_profile(profile_id)
        if record is None:
            raise ChemistryError(404, "Profile not found.")
        return record, self.repository.list_measurements([profile_id])

    def get_public_specimen_profiles(self, specimen_id: str):
        if not self.repository.specimen_exists(specimen_id):
            raise ChemistryError(404, "Specimen not found.")
        return self.repository.list_released_specimen_profiles(specimen_id)
