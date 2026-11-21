"""This module contains the SpecimenRepository class.

This class is a repository for specimens, and provides methods to interact with the database
for storing and retrieving specimen records.
"""
from datetime import date
from sqlite3 import SQLITE_CONSTRAINT_UNIQUE
from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func, or_, select
from app.config import settings
from app.db import lock_for_update
from app.field_loc.models import FieldLoc
from app.specimen.models import Revision, ScientificCorrection, Specimen
from app.specimen.exceptions import (
    SearchResultsNotFoundException, SpecimenExceptionRegNo, SpecimenInUseException, SpecimenNotFoundException,
)
from app.specimen.schemas import SpecimenSchemaUpdate
from app.specimen.schemas.specimen_schemas import VoucherMetadata
from fastapi_pagination.ext.sqlalchemy import paginate
from app.storage.models import Storage
from app.taxonomy.models import Taxonomy
from app.users.models import User


class SpecimenRepository:
    """This class is a repository for specimens.

    It provides methods to create, read, update, and delete specimen records in the database,
    as well as methods to query and retrieve various statistics about the specimens.
    """

    def __init__(self, db: Session):
        """
        Initialize a new instance of the SpecimenRepository class
        :param db: The database session to use for database interactions
        :type db: Session
        """
        self.db = db

    def validate_foreign_keys(self, taxon_id: str, field_loc_id: str, storage_id: str,
                              collected_by: str, verified_by: str):
        """
        Check if provided foreign keys are valid
        :param taxon_id: The ID of the taxon to check
        :param field_loc_id: The ID of the field location to check
        :param storage_id: The ID of the storage to check
        :param collected_by: The ID of the collector to check
        :param verified_by: The ID of the verifier to check
        :raises ValueError: If any of the provided foreign keys are invalid
        """
        if taxon_id:
            if not self.db.query(Taxonomy).filter(Taxonomy.taxon_id
                                                  == taxon_id).first():
                raise ValueError(f"Invalid taxon_id: {taxon_id}")

        if field_loc_id:
            if not self.db.query(FieldLoc).filter(FieldLoc.field_loc_id
                                                  == field_loc_id).first():
                raise ValueError(f"Invalid field_loc_id: {field_loc_id}")
        if storage_id:
            if not self.db.query(Storage).filter(Storage.storage_id == storage_id).first():
                raise ValueError(f"Invalid storage_id: {storage_id}")
        if collected_by:
            if not self.db.query(User).filter(User.user_id == collected_by).first():
                raise ValueError(f"Invalid collected_by: {collected_by}")
        if verified_by:
            if not self.db.query(User).filter(User.user_id == verified_by).first():
                raise ValueError(f"Invalid verified_by: {verified_by}")

    def create_specimen(self, specimen):
        """Create a new specimen record in the database."""
        self.validate_foreign_keys(
            specimen.taxon_id, specimen.field_loc_id, specimen.storage_id,
            specimen.collected_by, specimen.verified_by,
        )
        record = Specimen(**specimen.model_dump())
        self.db.add(record)
        self._commit_specimen()
        self.db.refresh(record)
        return record

    def _commit_specimen(self):
        """Translate duplicate accession or legacy registration numbers."""
        try:
            self.db.commit()
        except IntegrityError as error:
            self.db.rollback()
            if (getattr(error.orig, "sqlite_errorcode", None) == SQLITE_CONSTRAINT_UNIQUE
                    or (error.orig.args and error.orig.args[0] == 1062)):
                raise SpecimenExceptionRegNo(
                    "This collection already has that accession, or the legacy registration number is in use.", 409
                ) from error
            raise

    def read_specimen_by_id(self, specimen_id: str):
        """
        This function takes in a specimen_id and returns the specimen object with that id
        :param specimen_id: str
        :type specimen_id: str
        :return: The specimen object is being returned.
        """
        specimen = self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first()
        if specimen is None:
            raise SpecimenNotFoundException(f"Specimen with the provided ID: "
                                            f"{specimen_id} not found.", 400)
        return specimen

    def delete_specimen(self, specimen_id: str):
        """
        It deletes a specimen from the database
        :param specimen_id: The ID of the specimen to be deleted
        :type specimen_id: str
        :return: True
        """
        try:
            query = self.db.query(Specimen).filter_by(specimen_id=specimen_id)
            specimen = lock_for_update(self.db, query).first()
            if specimen is None:
                raise SpecimenNotFoundException(f"Specimen with provided ID: "
                                                f"{specimen_id} not found.", 400)
            self.db.delete(specimen)
            self.db.commit()
            return True
        except IntegrityError as error:
            self.db.rollback()
            raise SpecimenInUseException(
                "Remove linked images and publications before deleting this specimen. "
                "Specimens with determination history, corrections, weather records "
                "or linked lab samples must be retained."
            ) from error

    def read_specimen_by_reg_num(self, reg_no: str):
        """
        It returns the first specimen in the database with the given registration number
        :param reg_no: str
        :type reg_no: str
        :return: The first row of the table that matches the query.
        """
        return self.db.query(Specimen).filter(Specimen.reg_no == reg_no).first()

    def get_specimens_per_year(self):
        """
        It returns a list of tuples, each tuple containing the
        year and the number of specimens collected in that year
        :return: A list of tuples, where each tuple is a year and
        the number of specimens collected in that year.
        """
        query = self.db.query(func.extract('year', Specimen.collection_date).label('year'),
                              func.count(Specimen.specimen_id).label('count')).\
            group_by('year').order_by(func.extract('year', Specimen.collection_date).desc())
        return query.all()

    def get_specimens_per_user(self):
        """
        It returns a dictionary of the form {'username': number of
        specimens collected by that user}

        :return: A dictionary with the name and surname of the user as the
        key and the number of specimens collected by that
        user as the value.
        """
        query = self.db.query(User.name, User.surname, func.count(Specimen.specimen_id)) \
            .join(Specimen, User.user_id == Specimen.collected_by) \
            .group_by(User.user_id).order_by(func.count(Specimen.specimen_id).desc())
        results = {}
        for name, surname, count in query.all():
            results[f"{name} {surname}"] = count
        return results

    def get_specimens_per_region(self):
        """
        Get the number of specimens per region
        :return: A dictionary with the region as the key and the number of specimens as the value.
        """
        result = self.db.query(FieldLoc.region, func.count(Specimen.specimen_id)) \
            .join(Specimen, Specimen.field_loc_id == FieldLoc.field_loc_id) \
            .group_by(FieldLoc.region) \
            .all()
        return {row[0]: row[1] for row in result}

    def get_gps_for_search_results(self, keyword: str):
        """
        Retrieve GPS locations for specimens matching a keyword in the subnomen.

        :param keyword: A keyword to search for in specimen subnomen.
        :type keyword: str

        :return: A dictionary mapping specimen registration numbers to GPS locations,
                 where each GPS location is a tuple of (latitude, longitude).
        :rtype: dict
        """
        gps_locations = {}
        specimens = self.db.query(Specimen, FieldLoc).join(FieldLoc).filter(
            Specimen.subnomen.like(f'%{keyword}%')).all()
        for specimen, field_loc in specimens:
            gps_locations[specimen.reg_no or specimen.specimen_id] \
                = {"subnomen": specimen.subnomen, "gps": (field_loc.gps_lat, field_loc.gps_long)}
        if not gps_locations:
            raise SearchResultsNotFoundException(message="Search query returned empty results.",
                                                 code=404)
        return gps_locations

    def get_last_specimens(self):
        """
        It returns the last 10 specimens registered in the database
        :return: The last 10 specimens in the database.
        """
        return self.db.query(Specimen).order_by(
            Specimen.reg_date.desc()).limit(10).all()

    def get_herbarium_label(self, reg_no: str | None = None, *, specimen_id: str | None = None):
        """
        It takes a registration number as an argument, and returns a dictionary
        containing the details of the specimen with
        that registration number
        :param reg_no: The registration number of the specimen
        :type reg_no: str
        :return: A dictionary with the specimen's registration number,
        species, country, region, altitude, GPS coordinates,
        habitat, collection date, the name of the person who
        collected the specimen, and the name of the person who verified
        the specimen.
        """
        if bool(reg_no) == bool(specimen_id):
            raise ValueError("Provide either specimen_id or reg_no.")
        specimen = self.db.get(Specimen, specimen_id) if specimen_id else self.read_specimen_by_reg_num(reg_no)
        if specimen is None:
            raise SpecimenExceptionRegNo(message="No such specimen in the database.", code=404)
        location = specimen.field_loc
        label = {
            "specimen_id": specimen.specimen_id,
            "reg_no": specimen.reg_no,
            "subnomen": specimen.subnomen,
            "country": location.country if location else None,
            "region": location.region if location else None,
            "altitude": location.altitude if location else None,
            "gps": (location.gps_lat, location.gps_long) if location else None,
            "habitat": location.habitat if location else None,
            "coordinate_uncertainty_m": location.coordinate_uncertainty_m if location else None,
            "geodetic_datum": location.geodetic_datum if location else None,
            "collection_date": specimen.collection_date,
            "collected_by": specimen.collector_name or self.get_user_name(specimen.collected_by),
            "collector_number": specimen.collector_number,
            "verbatim_collection_date": specimen.verbatim_collection_date,
            "type_status": specimen.type_status,
            "verified_by": specimen.verifier_name or self.get_user_name(specimen.verified_by),
            "holding_type": specimen.holding_type,
            "holding_institution": specimen.holding_institution,
            "collection": specimen.collection,
            "accession": specimen.accession,
            "verbatim_label": specimen.verbatim_label,
            "determiner_name": specimen.determiner_name,
            "determination_date": specimen.determination_date,
        }
        return label

    def get_user_name(self, user_id: str):
        """
        It returns the name and surname of a user with a given user_id
        :param user_id: str - the user's id
        :type user_id: str
        :return: The name and surname of the user with the given user_id.
        """
        user = self.db.get(User, user_id) if user_id else None
        return f"{user.name} {user.surname}" if user else None

    def _apply_update(self, specimen_id, changes, revised_by, correction_reason=None, *, new_determination=False):
        query = self.db.query(Specimen).filter_by(specimen_id=specimen_id)
        specimen = lock_for_update(self.db, query).first()
        if specimen is None:
            return None, None
        self.validate_foreign_keys(*(changes.get(key) for key in (
            "taxon_id", "field_loc_id", "storage_id", "collected_by", "verified_by"
        )))
        names = {"taxon_id", "subnomen"}
        if not correction_reason and any(key in changes and getattr(specimen, key) != changes[key] for key in names):
            changes.setdefault("determiner_name", None)
            changes.setdefault("determination_date", None)
        changes = {key: value for key, value in changes.items() if getattr(specimen, key) != value}
        determination_fields = names | {"determiner_name", "determination_date"}
        if changes and (correction_reason is not None or changes.keys() - determination_fields
                        or not (new_determination or names.intersection(changes))):
            self.db.add(ScientificCorrection(
                specimen_id=specimen_id, actor_id=revised_by, reason=correction_reason,
                old_values={key: getattr(specimen, key) for key in changes}, new_values=changes,
            ))
        revision = None
        if determination_fields.intersection(changes):
            if not revised_by:
                raise ValueError("An authenticated curator is required to change identification.")
            revision = Revision(revised_by, specimen_id, specimen.taxon_id, specimen.subnomen,
                                specimen.determiner_name, specimen.determination_date)
            self.db.add(revision)
        for field, value in changes.items():
            setattr(specimen, field, value)
        return specimen, revision

    def update_specimen(self, specimen_id: str, specimen: SpecimenSchemaUpdate, revised_by=None):
        changes = {
            field: value for field, value in specimen.model_dump(exclude={"correction_reason"}, exclude_unset=True).items()
            if field in VoucherMetadata.model_fields or value not in (None, "")
        }
        updated, _ = self._apply_update(specimen_id, changes, revised_by, specimen.correction_reason)
        if updated is not None:
            self._commit_specimen()
            if self.db.expire_on_commit:
                self.db.refresh(updated)
        return updated

    def revise_identification(self, specimen_id: str, changes: dict, revised_by: str):
        specimen, revision = self._apply_update(specimen_id, changes, revised_by, new_determination=True)
        if specimen is None:
            raise SpecimenNotFoundException("Specimen not found.", 404)
        if revision is None:
            raise ValueError("The requested identification is already recorded.")
        self.db.commit()
        self.db.refresh(revision)
        return revision

    def get_specimens_by_date_range(self, start_date: date, end_date: date):
        """
        Returns a list of specimens that were collected between the specified start and end dates
        :param start_date: The start date of the date range
        :param end_date: The end date of the date range
        """
        return self.db.query(Specimen).filter(Specimen.collection_date >= start_date,
                                              Specimen.collection_date <= end_date).all()

    def get_specimens_by_distance(self, keyword: str):
        """
        Get specimens by distance from a given keyword.

        :param keyword: The keyword to search for in the subnomen of species.
        :type keyword: str

        :return: A list of dictionaries representing the specimens, sorted by distance.
        :rtype: List[Dict[str, Union[str, int]]]
        """
        lat = settings.LATITUDE
        long = settings.LONGITUDE
        specimens = self.db.query(Specimen, FieldLoc).filter(
            Specimen.subnomen.like(f'%{keyword}%'),
            Specimen.field_loc_id == FieldLoc.field_loc_id).all()
        results = []
        for specimen, field_loc in specimens:
            coordinates = field_loc.gps_lat, field_loc.gps_long
            distance = -1 if None in coordinates else geodesic((lat, long), coordinates).kilometers
            results.append({
                "reg_no": specimen.reg_no,
                "specimen_id": specimen.specimen_id,
                "subnomen": specimen.subnomen,
                "distance": round(distance)
            })
        return sorted(results, key=lambda x: x["distance"])

    def search_specimens_by_keyword(self, keyword: str, params):
        query = select(Specimen)
        if keyword:
            query = query.where(or_(
                Specimen.subnomen.icontains(keyword, autoescape=True),
                Specimen.accession.icontains(keyword, autoescape=True),
                Specimen.reg_no.icontains(keyword, autoescape=True),
            ))
        return paginate(self.db, query.order_by(Specimen.reg_no, Specimen.accession, Specimen.specimen_id), params=params)
