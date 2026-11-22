"""Database operations for studies, profiles, and saved analyses."""

from sqlalchemy import exists, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.chemistry.exceptions import ChemistryError
from app.chemistry.models import (ChemistryStructure, Compound, LabSample, Measurement, MeasurementCorrection,
                                  Preparation, Profile, SampleVoucher, Study)
from app.field_loc.models import FieldLoc
from app.publication.models import Publication
from app.specimen.models import Specimen
from app.chemistry.schemas.chemistry_schemas import VOUCHER_ROLES as ROLE_ORDER
from app.taxonomy.models import Taxonomy


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

    def get_specimens(self, specimen_ids: list[str]):
        rows = self.db.execute(
            select(Specimen, Taxonomy.taxon_name)
            .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
            .where(Specimen.specimen_id.in_(specimen_ids))
        ).all()
        return {specimen.specimen_id: (specimen, taxon_name) for specimen, taxon_name in rows}

    def field_loc_exists(self, field_loc_id: str):
        return self.db.get(FieldLoc, field_loc_id) is not None

    def public_specimen_exists(self, specimen_id: str):
        return self.db.scalar(select(Specimen.specimen_id).where(
            Specimen.specimen_id == specimen_id, Specimen.is_public.is_(True),
        )) is not None

    def list_study_samples(self, study_id: str):
        query = select(LabSample).where(LabSample.study_id == study_id).order_by(LabSample.code)
        return self.db.scalars(query).all()

    def list_sample_links(self, sample_ids):
        """Linked vouchers per sample as (link, voucher, current taxon name), in role order."""
        links = {sample_id: [] for sample_id in sample_ids}
        if not links:
            return links
        rows = self.db.execute(
            select(SampleVoucher, Specimen, Taxonomy.taxon_name)
            .join(Specimen, Specimen.specimen_id == SampleVoucher.specimen_id)
            .outerjoin(Taxonomy, Taxonomy.taxon_id == Specimen.taxon_id)
            .where(SampleVoucher.sample_id.in_(list(links)))
            .order_by(SampleVoucher.sample_id, SampleVoucher.specimen_id)
        ).all()
        for link, specimen, taxon_name in rows:
            links[link.sample_id].append((link, specimen, taxon_name))
        for rows in links.values():
            rows.sort(key=lambda row: (ROLE_ORDER.index(row[0].role), row[0].specimen_id))
        return links

    def get_link(self, sample_id: str, specimen_id: str):
        return self.db.get(SampleVoucher, (sample_id, specimen_id))

    def count_links(self, sample_id: str):
        return self.db.scalar(select(func.count()).where(SampleVoucher.sample_id == sample_id))

    def sample_has_public_profile(self, sample_id: str):
        return self.db.scalar(
            select(Profile.id).join(Preparation, Preparation.id == Profile.preparation_id)
            .where(Preparation.sample_id == sample_id, Profile.is_public.is_(True)).limit(1)
        ) is not None

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
        unreleased_voucher = (
            select(SampleVoucher.sample_id)
            .join(Specimen, Specimen.specimen_id == SampleVoucher.specimen_id)
            .where(SampleVoucher.sample_id == LabSample.id, Specimen.is_public.is_not(True))
        )
        any_voucher = select(SampleVoucher.sample_id).where(SampleVoucher.sample_id == LabSample.id)
        # Every linked voucher must be released, and a sample always has at least one.
        return (cls._profile_records()
                .join(Study, Study.id == LabSample.study_id)
                .where(Study.is_public.is_(True), Profile.is_public.is_(True),
                       exists(any_voucher), ~exists(unreleased_voucher)))

    def list_released_study_profiles(self, study_id: str):
        query = (self._released_profiles().where(LabSample.study_id == study_id)
                 .order_by(LabSample.code, Profile.run_code, Profile.id))
        return self.db.execute(query).all()

    def list_released_specimen_profiles(self, specimen_id: str):
        linked = select(SampleVoucher.sample_id).where(
            SampleVoucher.sample_id == LabSample.id, SampleVoucher.specimen_id == specimen_id)
        query = (self._released_profiles().where(exists(linked))
                 .order_by(Study.title, LabSample.code, Profile.run_code, Profile.id))
        return self.db.execute(query).all()

    def get_released_profile(self, profile_id: str):
        return self.db.execute(self._released_profiles().where(Profile.id == profile_id)).one_or_none()

    def list_measurements(self, profile_ids: list[str]):
        """Measurements with their registered compound (or None), ordered by feature."""
        query = (select(Measurement, Compound).outerjoin(Compound, Compound.cid == Measurement.cid)
                 .where(Measurement.profile_id.in_(profile_ids)).order_by(Measurement.feature))
        return self.db.execute(query).all()

    def get_compound(self, cid: int):
        return self.db.get(Compound, cid)

    def list_released_structure_profiles(self, structure_id: str):
        """Released profiles with a measurement of this author-supplied structure."""
        used = select(Measurement.profile_id).where(Measurement.structure_id == structure_id)
        return self.db.execute(self._released_profiles().where(Profile.id.in_(used))
                               .order_by(LabSample.code, Profile.run_code)).all()

    def get_public_structure(self, structure_id: str):
        """An author-supplied structure, once a released profile reports it; until then it is unpublished."""
        structure = self.db.get(ChemistryStructure, structure_id)
        if structure is None or not self.list_released_structure_profiles(structure_id):
            return None
        return structure

    def get_measurement(self, profile_id: str, feature: str):
        return self.db.get(Measurement, (profile_id, feature))

    def list_corrections(self, profile_ids: list[str]):
        query = (select(MeasurementCorrection).where(MeasurementCorrection.profile_id.in_(profile_ids))
                 .order_by(MeasurementCorrection.corrected_at, MeasurementCorrection.id))
        return self.db.scalars(query).all()

    def save(self, *records):
        self.db.add_all(records)
        self._commit()

    def delete(self, record):
        self.db.delete(record)
        self._commit()

    def _commit(self):
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            raise ChemistryError(409, "A matching record already exists or a linked record changed.") from error

    def save_profile(self, profile: Profile, rows: list[dict], commit=True):
        self.db.add(profile)
        try:
            self.db.flush()
        except IntegrityError as error:
            self.db.rollback()
            raise ChemistryError(409, "A profile with that run code already exists for this batch.") from error
        self.db.add_all(Measurement(profile_id=profile.id, **row) for row in rows)
        if commit:
            self._commit()
        else:
            self.db.flush()
