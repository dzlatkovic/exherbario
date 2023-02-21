"""This module contains the SpecimenRepository class.

This class is a repository for specimens, and provides methods to interact with the database
for storing and retrieving specimen records.
"""
from datetime import date
from geopy.distance import geodesic
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from sqlalchemy import func, distinct

from app.field_loc.models import FieldLoc
from app.photos.models import Photos
from app.specimen.models import Specimen
from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.schemas import SpecimenSchemaUpdate
from app.storage.models import Storage
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

    def validate_foreign_keys(self, field_loc_id: str, storage_id: str, photos_id: str,
                              collected_by: str, verified_by: str):
        """
        Check if provided foreign keys are valid
        :param field_loc_id: The ID of the field location to check
        :param storage_id: The ID of the storage to check
        :param photos_id: The ID of the photos to check
        :param collected_by: The ID of the collector to check
        :param verified_by: The ID of the verifier to check
        :raises ValueError: If any of the provided foreign keys are invalid
        """
        if field_loc_id:
            if not self.db.query(FieldLoc).filter(FieldLoc.field_loc_id
                                                  == field_loc_id).first():
                raise ValueError(f"Invalid field_loc_id: {field_loc_id}")
        if storage_id:
            if not self.db.query(Storage).filter(Storage.storage_id == storage_id).first():
                raise ValueError(f"Invalid storage_id: {storage_id}")
        if photos_id:
            if not self.db.query(Photos).filter(Photos.photos_id == photos_id).first():
                raise ValueError(f"Invalid photos_id: {photos_id}")
        if collected_by:
            if not self.db.query(User).filter(User.user_id == collected_by).first():
                raise ValueError(f"Invalid collected_by: {collected_by}")
        if verified_by:
            if not self.db.query(User).filter(User.user_id == verified_by).first():
                raise ValueError(f"Invalid verified_by: {verified_by}")

    def create_specimen(self, reg_no: str, collection_date: str, reg_date: str,
                        family: str, genus: str, species: str, subnomen: str,
                        field_loc_id: str, storage_id: str, photos_id: str,
                        collected_by: str, verified_by: str):
        """Create a new specimen record in the database."""
        if self.db.query(Specimen).filter_by(photos_id=photos_id).first():
            raise ValueError('A specimen with the same photos_id already exists in the database')
        try:
            self.validate_foreign_keys(field_loc_id, storage_id, photos_id, collected_by,
                                       verified_by)
            specimen = Specimen(reg_no, collection_date, reg_date, family,
                                genus, species, subnomen, field_loc_id, storage_id,
                                photos_id, collected_by, verified_by)
            self.db.add(specimen)
            self.db.commit()
            self.db.refresh(specimen)
            return specimen
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

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
            specimen = self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first()
            if specimen is None:
                raise SpecimenNotFoundException(f"Specimen with provided ID: "
                                                f"{specimen_id} not found.", 400)
            self.db.delete(specimen)
            self.db.commit()
            return True
        except Exception as error:
            raise error

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
                              func.count(Specimen.specimen_id).label('count')).group_by('year').order_by(
            func.extract('year', Specimen.collection_date).desc())
        return query.all()

    def get_specimens_per_user(self):
        """
        It returns a dictionary of the form {'username': number of
        specimens collected by that user}

        The first line of the function is a query that returns a list of
        tuples of the form (username, user surname, number of specimens
        collected by that user)
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

    def count_specimens(self):
        """
        It counts the number of specimens, families, genus, and species in the database
        :return: A dictionary with the counts of specimens, families, genus, and species.
        """
        cnt_specimens = self.db.query(func.count(Specimen.specimen_id)).scalar()
        cnt_families = self.db.query(func.count(distinct(Specimen.family))).scalar()
        cnt_genus = self.db.query(func.count(distinct(Specimen.genus))).scalar()
        cnt_species = self.db.query(func.count(distinct(Specimen.species))).scalar()
        return {"cnt_specimens": cnt_specimens,
                "cnt_families": cnt_families,
                "cnt_genus": cnt_genus,
                "cnt_species": cnt_species}

    def get_gps_for_genus(self, genus: str):
        """
        This function takes a genus name as an argument and returns a
        dictionary of species names and their GPS
        coordinates
        :param genus: The genus of the specimen you want to get the
        GPS coordinates for
        :type genus: str
        :return: A dictionary of the genus and species of the specimen
        and the gps coordinates of the field location.
        """
        gps_locations = {}
        specimens = self.db.query(Specimen, FieldLoc).join(FieldLoc).filter(
            Specimen.genus == genus).all()
        for specimen, field_loc in specimens:
            gps_locations[f"{specimen.genus} {specimen.species}"] \
                = (field_loc.gps_lat, field_loc.gps_long)
        return gps_locations

    def get_last_specimens(self):
        """
        It returns the last 10 specimens registered in the database
        :return: The last 10 specimens in the database.
        """
        return self.db.query(Specimen).order_by(
            Specimen.reg_date.desc()).limit(10).all()

    def get_herbarium_label(self, reg_no: str):
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
        specimen = self.db.query(Specimen).filter_by(reg_no=reg_no).first()
        label = {
            "reg_no": specimen.reg_no,
            "species": f"{specimen.genus} {specimen.species}",
            "country": specimen.field_loc.country,
            "region": specimen.field_loc.region,
            "altitude": specimen.field_loc.altitude,
            "gps": (specimen.field_loc.gps_lat, specimen.field_loc.gps_long),
            "habitat": specimen.field_loc.habitat,
            "collection_date": specimen.collection_date,
            "collected_by": self.get_user_name(specimen.collected_by),
            "verified_by": self.get_user_name(specimen.verified_by)
        }
        return label

    def get_user_name(self, user_id: str):
        """
        It returns the name and surname of a user with a given user_id
        :param user_id: str - the user's id
        :type user_id: str
        :return: The name and surname of the user with the given user_id.
        """
        user = self.db.query(User).filter_by(user_id=user_id).first()
        return f"{user.name} {user.surname}"

    def update_specimen(self, specimen_id: str, specimen: SpecimenSchemaUpdate):
        """
        It updates the specimen with the given specimen_id with the given specimen
        :param specimen_id: str
        :type specimen_id: str
        :param specimen: SpecimenSchemaUpdate
        :type specimen: SpecimenSchemaUpdate
        :return: The updated specimen.
        """
        self.validate_foreign_keys(specimen.field_loc_id, specimen.storage_id,
                                   specimen.photos_id, specimen.collected_by, specimen.verified_by)
        db_specimen = self.db.query(Specimen).filter(Specimen.specimen_id == specimen_id).first()
        if db_specimen:
            if specimen.reg_no:
                db_specimen.reg_no = specimen.reg_no
            if specimen.collection_date:
                db_specimen.collection_date = specimen.collection_date
            if specimen.family:
                db_specimen.family = specimen.family
            if specimen.genus:
                db_specimen.genus = specimen.genus
            if specimen.species:
                db_specimen.species = specimen.species
            if specimen.subnomen:
                db_specimen.subnomen = specimen.subnomen
            if specimen.field_loc_id:
                db_specimen.field_loc_id = specimen.field_loc_id
            if specimen.storage_id:
                db_specimen.storage_id = specimen.storage_id
            if specimen.photos_id:
                db_specimen.photos_id = specimen.photos_id
            if specimen.collected_by:
                db_specimen.collected_by = specimen.collected_by
            if specimen.verified_by:
                db_specimen.verified_by = specimen.verified_by
            self.db.commit()
            self.db.refresh(db_specimen)
            return db_specimen
        return None

    def get_specimens_by_date_range(self, start_date: date, end_date: date):
        """
        Returns a list of specimens that were collected between the specified start and end dates
        :param start_date: The start date of the date range
        :param end_date: The end date of the date range
        """
        return self.db.query(Specimen).filter(Specimen.collection_date >= start_date,
                                              Specimen.collection_date <= end_date).all()

    def get_specimens_by_genus_and_distance(self, genus: str):
        lat = 43.3097167
        long = 21.9231889
        specimens = self.db.query(Specimen, FieldLoc).filter(
            Specimen.genus == genus,
            Specimen.field_loc_id == FieldLoc.field_loc_id).all()
        results = []
        for specimen, field_loc in specimens:
            distance = geodesic((lat, long), (field_loc.gps_lat, field_loc.gps_long)).kilometers
            results.append({
                "reg_no": specimen.reg_no,
                "subnomen": specimen.subnomen,
                "distance": distance
            })
        return sorted(results, key=lambda x: x["distance"])
