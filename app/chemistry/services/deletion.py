"""Delete private chemistry records and clean up their unreferenced uploads."""

from logging import getLogger

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import (LabSample, Measurement, MeasurementCorrection, Preparation, Profile,
                                  SampleVoucher, SpreadsheetImport, Study)
from app.db import lock_for_update
from app.deposition.references import draft_reference
from app.file_storage import FILES_ROOT, archive_member

logger = getLogger(__name__)


class ChemistryDeletion:
    def __init__(self, db: Session):
        self.db = db

    def _record(self, model, record_id, label):
        record = lock_for_update(self.db, self.db.query(model).filter_by(id=record_id)).first()
        if record is None:
            raise ChemistryError(404, f"{label} not found.")
        return record

    def _study(self, study_id, actor):
        study = self._record(Study, study_id, "Study")
        if not actor.is_superuser and study.owner_id != actor.user_id:
            raise ChemistryError(404, "Study not found.")
        return study

    @staticmethod
    def _require_private(record, label):
        if record.is_public or record.ever_public:
            raise ChemistryError(409, f"{label} has been released and must be retained.")

    def _check_runs(self, profiles, actor):
        for profile in profiles:
            self._require_private(profile, f"Run {profile.run_code}")
        draft = draft_reference(self.db, "profile_ids", {profile.id for profile in profiles}, actor)
        if draft:
            raise ChemistryError(409, f"Remove the linked runs from {draft} before deleting.")

    def _delete_runs(self, profile_ids):
        if profile_ids:
            self.db.execute(delete(MeasurementCorrection).where(MeasurementCorrection.profile_id.in_(profile_ids)))
            self.db.execute(delete(Measurement).where(Measurement.profile_id.in_(profile_ids)))
            self.db.execute(delete(Profile).where(Profile.id.in_(profile_ids)))

    def _commit(self, sources=()):
        self.db.commit()
        for source in set(sources) - {None}:
            if any(self.db.scalar(select(model.id).where(model.source_path == source).limit(1))
                   for model in (Profile, SpreadsheetImport)):
                continue
            try:
                archive_member(FILES_ROOT, source).unlink(missing_ok=True)
            except (OSError, ValueError):
                logger.exception("Could not remove unreferenced chemistry upload %s", source)

    def delete_study(self, study_id, actor, expected_counts=None):
        study = self._study(study_id, actor)
        self._require_private(study, "This study")
        samples = list(self.db.scalars(select(LabSample.id).where(LabSample.study_id == study_id)))
        preparations = list(self.db.scalars(select(Preparation.id).where(Preparation.sample_id.in_(samples))))
        profiles = list(self.db.scalars(select(Profile).where(Profile.preparation_id.in_(preparations))))
        imports = list(self.db.scalars(select(SpreadsheetImport).where(SpreadsheetImport.study_id == study_id)))
        if expected_counts is not None and expected_counts != (len(samples), len(preparations), len(profiles), len(imports)):
            raise ChemistryError(409, "The study contents changed. Reload the page and review them before deleting.")
        self._check_runs(profiles, actor)
        sources = [row.source_path for row in [*profiles, *imports]]
        self._delete_runs([profile.id for profile in profiles])
        self.db.execute(delete(SpreadsheetImport).where(SpreadsheetImport.study_id == study_id))
        self.db.execute(delete(Preparation).where(Preparation.id.in_(preparations)))
        self.db.execute(delete(SampleVoucher).where(SampleVoucher.sample_id.in_(samples)))
        self.db.execute(delete(LabSample).where(LabSample.study_id == study_id))
        self.db.delete(study)
        self._commit(sources)

    def delete_sample(self, sample_id, actor):
        sample = self._record(LabSample, sample_id, "Sample")
        study = self._study(sample.study_id, actor)
        self._require_private(study, "This study")
        if self.db.scalar(select(Preparation.id).where(Preparation.sample_id == sample_id).limit(1)):
            raise ChemistryError(409, "Remove the sample’s preparations before deleting it.")
        self.db.execute(delete(SampleVoucher).where(SampleVoucher.sample_id == sample_id))
        self.db.delete(sample)
        self._commit()

    def delete_preparation(self, preparation_id, actor):
        preparation = self._record(Preparation, preparation_id, "Preparation")
        sample = self.db.get(LabSample, preparation.sample_id)
        study = self._study(sample.study_id, actor)
        self._require_private(study, "This study")
        if self.db.scalar(select(Profile.id).where(Profile.preparation_id == preparation_id).limit(1)):
            raise ChemistryError(409, "Remove the preparation’s analytical runs before deleting it.")
        imports = self.db.scalars(select(SpreadsheetImport.assignment).where(
            SpreadsheetImport.study_id == study.id, SpreadsheetImport.status == "draft"))
        if any(column.get("preparation_id") == preparation_id
               for assignment in imports for column in (assignment or {}).get("columns", [])):
            raise ChemistryError(409, "An unfinished import uses this preparation. Reassign its column or discard the import first.")
        self.db.delete(preparation)
        self._commit()

    def delete_profile(self, profile_id, actor):
        profile = self._record(Profile, profile_id, "Run")
        preparation = self.db.get(Preparation, profile.preparation_id)
        sample = self.db.get(LabSample, preparation.sample_id)
        self._study(sample.study_id, actor)
        self._check_runs([profile], actor)
        source = profile.source_path
        self._delete_runs([profile.id])
        self._commit([source])

    def discard_import(self, import_id, actor):
        record = self._record(SpreadsheetImport, import_id, "Import")
        if not actor.is_superuser and record.owner_id != actor.user_id:
            raise ChemistryError(404, "Import not found.")
        if record.status != "draft":
            raise ChemistryError(409, "Only an unfinished import can be discarded.")
        self.db.delete(record)
        self._commit([record.source_path])
