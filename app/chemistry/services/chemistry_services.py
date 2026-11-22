"""Study access, profile import, and analysis workflows."""

from contextlib import ExitStack
from hashlib import sha256
from pathlib import PurePosixPath
from typing import BinaryIO
from uuid import uuid4

from pydantic import ValidationError

from app.chemistry.sample_links import new_link, utc_now
from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, MeasurementCorrection, Preparation, Profile, Study
from app.chemistry.repository import ChemistryRepository
from app.chemistry.schemas import (Basis, CompoundCorrectionIn, PreparationIn, SampleIn, StudyIn, Technique,
                                   VoucherLinkIn, run_metadata_for)
from app.chemistry.schemas.chemistry_schemas import MAX_SAMPLE_VOUCHERS
from app.db import lock_for_update, new_id
from app.file_storage import FILES_ROOT, archive_member, store_upload
from app.users.models import User

from .compounds import CompoundRegistry
from .profile_import import MAX_CSV_BYTES, read_measurements


def validated_run(technique: str, run_metadata: dict | None) -> dict:
    try:
        return run_metadata_for(technique, run_metadata)
    except ValidationError as error:
        problems = "; ".join(f"{'.'.join(map(str, item['loc'])) or 'run metadata'}: {item['msg']}"
                             for item in error.errors())
        raise ChemistryError(422, f"Invalid run metadata for {technique}: {problems}") from error


class ChemistryService:
    def __init__(self, repository: ChemistryRepository, registry: CompoundRegistry | None = None):
        self.repository = repository
        self.registry = registry or CompoundRegistry(repository.db)

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
        study = Study(owner_id=actor.user_id, **data.model_dump())
        self.repository.save(study)
        return study

    def get_study(self, study_id: str, actor: User):
        study = self._study_for_actor(study_id, actor)
        samples = self.repository.list_study_samples(study_id)
        return (
            study,
            samples,
            self.repository.list_sample_links([sample.id for sample in samples]),
            self.repository.list_study_preparations(study_id),
            self.repository.list_study_profiles(study_id),
        )

    def _vouchers(self, specimen_ids: list[str]):
        found = self.repository.get_specimens(specimen_ids)
        missing = [specimen_id for specimen_id in specimen_ids if specimen_id not in found]
        if missing:
            raise ChemistryError(404, "Voucher specimen not found: " + ", ".join(missing))
        return found

    def create_sample(self, study_id: str, data: SampleIn, actor: User):
        self._study_for_actor(study_id, actor)
        vouchers = self._vouchers([link.specimen_id for link in data.vouchers])
        if data.field_loc_id and not self.repository.field_loc_exists(data.field_loc_id):
            raise ChemistryError(404, "Field location not found.")
        sample = LabSample(id=new_id(), study_id=study_id, **data.model_dump(exclude={"vouchers"}))
        links = [new_link(sample.id, *vouchers[link.specimen_id], link.role) for link in data.vouchers]
        self.repository.save(sample, *links)
        return sample

    def _sample_for_actor(self, sample_id: str, actor: User):
        sample = self.repository.get_sample(sample_id)
        if not sample:
            raise ChemistryError(404, "Sample not found.")
        self._study_for_actor(sample.study_id, actor)
        return sample

    def add_sample_voucher(self, sample_id: str, data: VoucherLinkIn, actor: User):
        sample = self._sample_for_actor(sample_id, actor)
        if self.repository.get_link(sample_id, data.specimen_id):
            raise ChemistryError(409, "This voucher is already linked to the sample.")
        if self.repository.count_links(sample_id) >= MAX_SAMPLE_VOUCHERS:
            raise ChemistryError(422, f"A sample can link at most {MAX_SAMPLE_VOUCHERS} vouchers.")
        specimen, taxon_name = self._vouchers([data.specimen_id])[data.specimen_id]
        link = new_link(sample.id, specimen, taxon_name, data.role)
        self.repository.save(link)
        return link

    def remove_sample_voucher(self, sample_id: str, specimen_id: str, actor: User):
        sample = self._sample_for_actor(sample_id, actor)
        link = self.repository.get_link(sample_id, specimen_id)
        if link is None:
            raise ChemistryError(404, "This voucher is not linked to the sample.")
        if self.repository.count_links(sample_id) == 1:
            raise ChemistryError(409, "A sample must stay linked to at least one voucher.")
        if sample.site_specimen_id == specimen_id:
            raise ChemistryError(409, "This voucher gives the sample's collection site.")
        if self.repository.sample_has_public_profile(sample_id):
            raise ChemistryError(409, "Withdraw the sample's released profiles before removing a voucher.")
        self.repository.delete(link)

    def create_preparation(self, sample_id: str, data: PreparationIn, actor: User):
        self._sample_for_actor(sample_id, actor)
        preparation = Preparation(sample_id=sample_id, **data.model_dump())
        self.repository.save(preparation)
        return preparation

    def import_profile(self, preparation_id: str, source_file: BinaryIO, source_name: str | None,
                       run_code: str, analytical_method: str, measurement_basis: Basis,
                       unit: str, actor: User, technique: Technique, run_metadata: dict | None = None):
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
        run = validated_run(technique, run_metadata)
        content = source_file.read(MAX_CSV_BYTES + 1)
        try:
            source, rows, warnings = read_measurements(content, measurement_basis, technique, run)
        except ValueError as error:
            raise ChemistryError(422, str(error)) from error
        for row in rows:
            # Identifiers in the author's own file are the author's assignment; register those compounds.
            identifiers = row.pop("identifiers")
            match = self.registry.lookup_identifiers(**identifiers) if identifiers else None
            if match:
                record, method = match
                row["cid"], row["compound_match"] = self.registry.register(record).cid, method
        filename = PurePosixPath((source_name or "profile.csv").replace("\\", "/")).name
        profile = self.store_profile(preparation_id, run_code, analytical_method, measurement_basis, unit, technique,
                                     run, filename, content, source, rows)
        return profile, warnings

    def store_profile(self, preparation_id, run_code, analytical_method, measurement_basis, unit, technique, run,
                      filename, content: bytes, source: str, rows, *, uploads: ExitStack | None = None, **extra):
        """Store a profile and its source file. With ``uploads``, the caller commits and the file is removed
        if the caller's transaction fails."""
        stored_path = (FILES_ROOT / f"{uuid4().hex}.csv").as_posix()
        profile = Profile(preparation_id=preparation_id, run_code=run_code,
                          analytical_method=analytical_method, measurement_basis=measurement_basis,
                          unit=unit, source_name=filename[:200] or "profile.csv", source_csv=source,
                          source_path=stored_path, source_sha256=sha256(content).hexdigest(),
                          technique=technique, run_metadata=run or None, **extra)
        try:
            if uploads is not None:
                uploads.enter_context(store_upload(archive_member(FILES_ROOT, stored_path), content))
                self.repository.save_profile(profile, rows, commit=False)
            else:
                with store_upload(archive_member(FILES_ROOT, stored_path), content):
                    self.repository.save_profile(profile, rows)
        except (OSError, ValueError) as error:
            raise ChemistryError(500, "Could not store the analytical file.") from error
        return profile

    def correct_compound(self, profile_id: str, feature: str, data: CompoundCorrectionIn, actor: User):
        """Reassign a measurement's compound. Values and the source file stay as they are; the change is logged."""
        self._profile_for_actor(profile_id, actor)
        measurement = self.repository.get_measurement(profile_id, feature)
        if measurement is None:
            raise ChemistryError(404, "Measurement not found.")
        if measurement.cid == data.cid:
            raise ChemistryError(409, "The measurement already has this compound assignment.")
        if data.cid is not None:
            self.registry.get(data.cid)
        correction = MeasurementCorrection(profile_id=profile_id, feature=measurement.feature, old_cid=measurement.cid,
                                           new_cid=data.cid, actor_id=actor.user_id, reason=data.reason,
                                           corrected_at=utc_now())
        measurement.cid = data.cid
        measurement.compound_match = "correction" if data.cid else "unidentified"
        self.repository.save(correction)
        return correction

    def get_profile(self, profile_id: str, actor: User):
        profile = self._profile_for_actor(profile_id, actor)
        return (profile, self.repository.list_measurements([profile_id]),
                self.repository.list_corrections([profile_id]))

    def get_profile_source(self, profile_id: str, actor: User) -> tuple[bytes, Profile]:
        profile = self._profile_for_actor(profile_id, actor)
        return self.read_profile_source(profile), profile

    @staticmethod
    def read_profile_source(profile: Profile) -> bytes:
        if profile.source_path is None and profile.source_sha256 is None:
            return profile.source_csv.encode("utf-8")
        if not profile.source_path or not profile.source_sha256:
            raise ChemistryError(409, "The original analytical file reference is incomplete.")
        try:
            with archive_member(FILES_ROOT, profile.source_path).open("rb") as source:
                content = source.read(MAX_CSV_BYTES + 1)
        except (OSError, ValueError) as error:
            raise ChemistryError(409, "The original analytical file is missing or unreadable.") from error
        if len(content) > MAX_CSV_BYTES or sha256(content).hexdigest() != profile.source_sha256:
            raise ChemistryError(409, "The original analytical file failed SHA-256 verification.")
        return content

    def set_study_visibility(self, study_id: str, is_public: bool, actor: User):
        db = self.repository.db
        lock_for_update(db, db.query(Study).filter_by(id=study_id)).first()
        study = self._study_for_actor(study_id, actor)
        study.ever_public = study.ever_public or study.is_public or is_public
        study.is_public = is_public
        self.repository.save(study)
        return study

    def set_profile_visibility(self, profile_id: str, is_public: bool, actor: User):
        db = self.repository.db
        lock_for_update(db, db.query(Profile).filter_by(id=profile_id)).first()
        profile = self._profile_for_actor(profile_id, actor)
        profile.ever_public = profile.ever_public or profile.is_public or is_public
        profile.is_public = is_public
        self.repository.save(profile)
        return profile

    def get_public_study(self, study_id: str):
        study = self.repository.get_study(study_id)
        if not study or not study.is_public:
            raise ChemistryError(404, "Study not found.")
        profiles = self.repository.list_released_study_profiles(study_id)
        if not profiles:
            raise ChemistryError(404, "Study not found.")
        return study, profiles, self._links_for(profiles)

    def _links_for(self, records):
        return self.repository.list_sample_links(sorted({sample.id for _, _, sample in records}))

    def get_public_profile(self, profile_id: str):
        record = self.repository.get_released_profile(profile_id)
        if record is None:
            raise ChemistryError(404, "Profile not found.")
        return (record, self._links_for([record]), self.repository.list_measurements([profile_id]),
                self.repository.list_corrections([profile_id]))

    def get_public_specimen_profiles(self, specimen_id: str):
        if not self.repository.public_specimen_exists(specimen_id):
            raise ChemistryError(404, "Specimen not found.")
        profiles = self.repository.list_released_specimen_profiles(specimen_id)
        return profiles, self._links_for(profiles)
