"""Database operations for studies, profiles, and saved analyses."""

from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import LabSample, Measurement, PCAAnalysis, Preparation, Profile, Study
from app.publication.models import Publication
from app.specimen.models import Specimen


class ChemistryRepository:
    def __init__(self, db: Session):
        self.db = db

    def list_studies(self, owner_id: str | None = None):
        query = select(Study).order_by(Study.title, Study.id)
        if owner_id is not None:
            query = query.where(Study.owner_id == owner_id)
        return self.db.scalars(query).all()

    def get_study(self, study_id: str):
        return self.db.get(Study, study_id)

    def get_sample(self, sample_id: str):
        return self.db.get(LabSample, sample_id)

    def get_preparation(self, preparation_id: str):
        return self.db.get(Preparation, preparation_id)

    def get_profile(self, profile_id: str):
        return self.db.get(Profile, profile_id)

    def publication_exists(self, publication_id: str):
        return self.db.get(Publication, publication_id) is not None

    def specimen_exists(self, specimen_id: str):
        return self.db.get(Specimen, specimen_id) is not None

    def list_study_samples(self, study_id: str):
        query = (select(LabSample, Specimen.reg_no).join(Specimen)
                 .where(LabSample.study_id == study_id).order_by(LabSample.code))
        return self.db.execute(query).all()

    def list_study_preparations(self, study_id: str):
        query = (select(Preparation).join(LabSample)
                 .where(LabSample.study_id == study_id).order_by(Preparation.batch_code))
        return self.db.scalars(query).all()

    @staticmethod
    def _profile_records():
        return (select(Profile, Preparation, LabSample)
                .join(Preparation, Preparation.id == Profile.preparation_id)
                .join(LabSample, LabSample.id == Preparation.sample_id))

    def list_study_profiles(self, study_id: str, profile_ids: list[str] | None = None):
        query = self._profile_records().where(LabSample.study_id == study_id)
        if profile_ids is not None:
            query = query.where(Profile.id.in_(profile_ids))
        return self.db.execute(query.order_by(LabSample.code, Profile.run_code)).all()

    def get_preparation_study_id(self, preparation_id: str):
        query = select(LabSample.study_id).join(Preparation).where(Preparation.id == preparation_id)
        return self.db.scalar(query)

    @classmethod
    def _released_profiles(cls):
        return cls._profile_records().join(Study, Study.id == LabSample.study_id).where(
            Study.is_public.is_(True), Profile.is_public.is_(True)
        )

    def list_released_study_profiles(self, study_id: str):
        query = (self._released_profiles().where(LabSample.study_id == study_id)
                 .order_by(LabSample.code, Profile.run_code, Profile.id))
        return self.db.execute(query).all()

    def list_released_specimen_profiles(self, specimen_id: str):
        query = (self._released_profiles().where(LabSample.specimen_id == specimen_id)
                 .order_by(Study.title, LabSample.code, Profile.run_code, Profile.id))
        return self.db.execute(query).all()

    def get_released_profile(self, profile_id: str):
        return self.db.execute(self._released_profiles().where(Profile.id == profile_id)).one_or_none()

    def list_measurements(self, profile_ids: list[str]):
        query = (select(Measurement).where(Measurement.profile_id.in_(profile_ids))
                 .order_by(Measurement.feature))
        return self.db.scalars(query).all()

    def list_study_analyses(self, study_id: str):
        query = (select(PCAAnalysis.id, PCAAnalysis.created_at)
                 .where(PCAAnalysis.study_id == study_id).order_by(PCAAnalysis.created_at.desc()))
        return self.db.execute(query).all()

    def get_analysis(self, study_id: str, analysis_id: str):
        query = select(PCAAnalysis).where(
            PCAAnalysis.study_id == study_id, PCAAnalysis.id == analysis_id
        )
        return self.db.scalar(query)

    def save(self, record):
        self.db.add(record)
        self._commit()

    def _commit(self):
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ChemistryError(409, "A matching record already exists or a linked record changed.") from error

    def save_profile(self, profile: Profile, rows: list[dict]):
        self.db.add(profile)
        try:
            self.db.flush()
        except IntegrityError as error:
            self.db.rollback()
            raise ChemistryError(409, "A profile with that run code already exists for this batch.") from error
        self.db.add_all(Measurement(profile_id=profile.id, **row) for row in rows)
        self._commit()
