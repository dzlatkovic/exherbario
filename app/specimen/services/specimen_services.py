"""This module contains the SpecimenService class."""

from datetime import datetime
import io
from fastapi import Response
import qrcode
from app.db import SessionLocal
from app.specimen.repository import SpecimenRepository
from app.specimen.exceptions import (SpecimenExceptionRegNo,
                                     SpecimenNotFoundException,
                                     InvalidDateRangeException)
from app.specimen.schemas import SpecimenSchemaUpdate


class SpecimenService:
    """This class provides a service for managing specimens"""

    @staticmethod
    def create_new_specimen(reg_no: str, collection_date: str, reg_date: str,
                            family: str, genus: str, species: str, subnomen: str,
                            field_loc_id: str, storage_id: str, photos_id: str,
                            collected_by: str, verified_by: str):
        """Create a new specimen record in the database."""
        try:
            with SessionLocal() as db:
                if collection_date > reg_date:
                    raise InvalidDateRangeException(
                        message="Collection date cannot be after registration date",
                        code=400)
                repository = SpecimenRepository(db)
                publication = repository.read_specimen_by_reg_num(reg_no)
                if publication is None:
                    return repository.create_specimen(reg_no, collection_date, reg_date,
                                                      family, genus, species, subnomen,
                                                      field_loc_id, storage_id, photos_id,
                                                      collected_by, verified_by)
                raise SpecimenExceptionRegNo(message="Specimen already exists in the database.",
                                             code=400)
        except Exception as error:
            raise error

    @staticmethod
    def read_specimen_by_id(specimen_id: str):
        """
        It reads a specimen from the database by its id
        :param specimen_id: str
        :type specimen_id: str
        :return: A specimen object
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.read_specimen_by_id(specimen_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_specimen_by_id(specimen_id: str):
        """
        It deletes a specimen from the database by its id
        :param specimen_id: str
        :type specimen_id: str
        :return: The specimen_id of the specimen that was deleted.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.delete_specimen(specimen_id)
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_per_year():
        """
        It gets the number of specimens per year from the database
        :return: A list of dictionaries, each containing a year and a count.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                specimens_per_year = repository.get_specimens_per_year()
                return [{'year': year, 'count': count}
                        for year, count in specimens_per_year]
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_per_user():
        """
        It gets the number of specimens per user
        :return: A list of tuples with the user_id and the number of specimens they have.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_specimens_per_user()
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_per_region():
        """
        It gets the number of specimens per region
        :return: A list of dictionaries with the region
        and the number of specimens in that region.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_specimens_per_region()
        except Exception as error:
            raise error

    @staticmethod
    def count_specimens():
        """
        It creates a database session, creates a repository,
        and then calls the repository's count_specimens() method.
        :return: The number of specimens in the database.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.count_specimens()
        except Exception as error:
            raise error

    @staticmethod
    def get_gps_for_genus(genus: str):
        """
        > This function takes a genus name as a string and returns a list
        of GPS coordinates for all specimens of that genus
        :param genus: str
        :type genus: str
        :return: A list of GPS coordinates for a given genus.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_gps_for_genus(genus)
        except Exception as error:
            raise error

    @staticmethod
    def get_last_specimens():
        """
        It gets the last specimens from the database
        :return: A list of the last 10 specimens added to the database.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_last_specimens()
        except Exception as error:
            raise error

    @staticmethod
    def get_herbarium_label(reg_no: str):
        """
        It takes a registration number as a string, checks if the specimen
        exists in the database, and if it does, returns the herbarium label
        :param reg_no: str
        :type reg_no: str
        :return: The herbarium label of the specimen
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                if not repository.read_specimen_by_reg_num(reg_no):
                    raise SpecimenExceptionRegNo(message="No such specimen in the database",
                                                 code=400)
                return repository.get_herbarium_label(reg_no)
        except Exception as error:
            raise error

    @staticmethod
    def update_specimen(specimen_id: str, specimen: SpecimenSchemaUpdate):
        """
        This function updates a specimen in the database
        :param specimen_id: str - the id of the specimen to be updated
        :type specimen_id: str
        :param specimen: SpecimenSchemaUpdate
        :type specimen: SpecimenSchemaUpdate
        :return: The updated specimen.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                repository.validate_foreign_keys(specimen.field_loc_id, specimen.storage_id,
                                                 specimen.photos_id, specimen.collected_by,
                                                 specimen.verified_by)
                db_specimen = repository.update_specimen(specimen_id, specimen)
            if db_specimen is None:
                raise SpecimenNotFoundException(message="Specimen not found.", code=400)
            return db_specimen
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_by_date_range(start_date: str, end_date: str):
        """
        Returns a list of specimens that were collected between the specified start and end dates
        :param start_date: The start date of the date range in the format 'YYYY-MM-DD'.
        :param end_date: The start date of the date range in the format 'YYYY-MM-DD'.
        :return: List[Specimen]
        """
        try:
            with SessionLocal() as db:
                start_date_obj = datetime.strptime(start_date, "%Y-%m-%d").date()
                end_date_obj = datetime.strptime(end_date, "%Y-%m-%d").date()
                if start_date_obj > end_date_obj:
                    raise InvalidDateRangeException(message="Start date cannot be after end date",
                                                    code=400)
                repository = SpecimenRepository(db)
                return repository.get_specimens_by_date_range(start_date_obj, end_date_obj)
        except (ValueError, TypeError) as exc:
            raise ValueError("Invalid input format. "
                             "Please provide valid format: 'YYYY-MM-DD'") from exc
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_by_genus_and_distance(genus: str):
        """
        Returns a list of specimens for the specified genus
        sorted by distance from the specified location
        :param genus: The genus of the specimens to retrieve.
        :return: list[dict]: A list of dictionaries containing the registration
        number, subnomen, and distance of each specimen, sorted by distance.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.get_specimens_by_genus_and_distance(genus)
        except Exception as error:
            raise error

    @staticmethod
    def generate_qr_code(reg_no: str):
        """
        `generate_qr_code` takes a registration number of the specimen
        as a string and returns a QR code image containing the
        herbarium label
        :param reg_no: The registration number of the specimen
        :type reg_no: str
        :return: A QR code image
        """
        data = SpecimenService.get_herbarium_label(reg_no)
        string_to_add = "\n".join(f"{key}: {value}"
                                  for key, value in data.items())
        try:
            qr_code = qrcode.QRCode(
                version=None,
                error_correction=qrcode.constants.ERROR_CORRECT_L,
                box_size=10,
                border=4,
            )
            qr_code.add_data(string_to_add)
            qr_code.make(fit=True)
            img = qr_code.make_image(fill_color="black", back_color="white")
            with io.BytesIO() as output:
                img.save(output, "PNG")
                contents = output.getvalue()
            return Response(content=contents, media_type="image/png")
        except Exception as error:
            raise error

    @staticmethod
    def search_specimens_by_keyword(keyword: str):
        """
        It takes a keyword as a parameter, and returns a
        list of specimens that match the keyword
        :param keyword: str
        :type keyword: str
        :return: A list of specimens that match the keyword.
        """
        try:
            with SessionLocal() as db:
                repository = SpecimenRepository(db)
                return repository.search_specimens_by_keyword(keyword)
        except Exception as error:
            raise error
