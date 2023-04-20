"""
specimen controller layer
"""


from starlette.responses import JSONResponse, HTMLResponse
from fastapi import HTTPException, Response
from app.specimen.schemas import SpecimenSchemaUpdate
from app.specimen.services import SpecimenService
from app.specimen.exceptions import (SpecimenExceptionRegNo,
                                     SpecimenNotFoundException,
                                     InvalidDateRangeException,
                                     SearchResultsNotFoundException)


class SpecimenController:
    """This class is used to control the specimen"""

    @staticmethod
    def create_new_specimen(reg_no: str, collection_date: str, reg_date: str,
                            family: str, genus: str, species: str, subnomen: str,
                            field_loc_id: str, storage_id: str, photos_id: str,
                            collected_by: str, verified_by: str):
        """Create a new specimen record in the database.

        This method creates a new `Specimen` object with the specified field values, and saves it to
        the database using the `SpecimenService.create_new_specimen` method. If any errors occur,
        this method catches them and raises an appropriate `HTTPException` with the error message
        :param reg_no: The registration number for the specimen record
        :type reg_no: str
        :param collection_date: The date the specimen was collected, in "yyyy-mm-dd" format.
        :type collection_date: str
        :param reg_date: The date the specimen was registered, in "yyyy-mm-dd" format
        :type reg_date: str
        :param family: The family of the specimen
        :type family: str
        :param genus: The genus of the specimen
        :type genus: str
        :param species: The species of the specimen
        :type species: str
        :param subnomen: The subnomen of the specimen
        :type subnomen: str
        :param field_loc_id: The ID of the field location where the specimen was collected
        :type field_loc_id: str
        :param storage_id: The ID of the storage location where the specimen is stored
        :type storage_id: str
        :param photos_id: The ID of the photos associated with the specimen
        :type photos_id: str
        :param collected_by: The ID of the user who collected the specimen
        :type collected_by: str
        :param verified_by: The ID of the user who verified the specimen
        :type verified_by: str
        """
        try:
            return SpecimenService.create_new_specimen(reg_no, collection_date, reg_date,
                                                       family, genus, species, subnomen,
                                                       field_loc_id, storage_id, photos_id,
                                                       collected_by, verified_by)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except (SpecimenExceptionRegNo, InvalidDateRangeException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimen_by_id(specimen_id: str):
        """
        This function returns a specimen by its id
        :param specimen_id: The ID of the specimen to retrieve
        :type specimen_id: str
        :return: A specimen object
        """
        try:
            return SpecimenService.read_specimen_by_id(specimen_id)
        except SpecimenNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_specimen_by_id(specimen_id: str):
        """
        Delete a specimen by ID
        :param specimen_id: str - The ID of the specimen to be deleted
        :type specimen_id: str
        :return: A response object with the content and status code.
        """
        try:
            SpecimenService.delete_specimen_by_id(specimen_id)
            return Response(content=f"Specimen with ID: {specimen_id} deleted.", status_code=200)
        except SpecimenNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_per_year():
        """
        It returns a JSONResponse object containing the content of the
        get_specimens_per_year() function from the
        SpecimenService class
        :return: A JSONResponse object
        """
        try:
            content = SpecimenService.get_specimens_per_year()
            return JSONResponse(content=content)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_per_user():
        """
        It returns a JSON response containing the number of specimens per user
        :return: A list of specimens per user
        """
        try:
            content = SpecimenService.get_specimens_per_user()
            return JSONResponse(content=content)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_per_region():
        """
        It returns a JSON response containing the number of specimens per region
        :return: A JSONResponse object
        """
        try:
            content = SpecimenService.get_specimens_per_region()
            return JSONResponse(content=content)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def count_specimens():
        """
        It returns the number of specimens in the database
        :return: The number of specimens in the database.
        """
        try:
            content = SpecimenService.count_specimens()
            return JSONResponse(content=content)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_gps_for_search_result(keyword):
        """
        Retrieve GPS locations for search results based on a keyword.

        This method calls the `SpecimenService.get_gps_for_genus` method
        to retrieve GPS locations for search results that match the provided
        keyword. The keyword should be a part of the subnomen.

        :param keyword: A string representing the keyword used for searching.
        :type keyword: str
        :return: A JSONResponse containing the retrieved GPS locations.
        :rtype: JSONResponse
        :raises: HTTPException with appropriate status code and detail message in case of errors.
        """
        try:
            content = SpecimenService.get_gps_for_search_results(keyword)
            return JSONResponse(content=content)
        except SearchResultsNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def visualize_gps(keyword: str) -> HTMLResponse:
        try:
            html = SpecimenService.visualize_gps(keyword)
            return HTMLResponse(content=html)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_last_specimens():
        """
        It returns the last 10 specimens from the database
        :return: A list of the last 10 specimens
        """
        try:
            return SpecimenService.get_last_specimens()
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_herbarium_label(reg_no: str):
        """
        This function returns the herbarium label of a specimen given
        its registration number
        :param reg_no: str
        :type reg_no: str
        :return: A list of all the herbarium labels
        """
        try:
            return SpecimenService.get_herbarium_label(reg_no)
        except SpecimenExceptionRegNo as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def update_specimen(specimen_id: str, specimen: SpecimenSchemaUpdate):
        """
        It updates a specimen in the database
        :param specimen_id: str - the id of the specimen to update
        :type specimen_id: str
        :param specimen: SpecimenSchemaUpdate
        :type specimen: SpecimenSchemaUpdate
        :return: The updated specimen
        """
        try:
            return SpecimenService.update_specimen(specimen_id, specimen)
        except SpecimenNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_by_date_range(start_date: str, end_date: str):
        """
        Returns a list of specimens that were collected between the specified start and end dates
        :param start_date: The start date of the date range in the format 'YYYY-MM-DD'.
        :param end_date: The start date of the date range in the format 'YYYY-MM-DD'.
        :return: List[Specimen]
        """
        try:
            return SpecimenService.get_specimens_by_date_range(start_date, end_date)
        except InvalidDateRangeException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_by_distance(keyword: str):
        """
        Get specimens by distance from a given keyword.

        :param keyword: The keyword to search for in the subnomen of species.
        :type keyword: str

        :raises: HTTPException: If any error occurs during processing.
        """
        try:
            return SpecimenService.get_specimens_by_distance(keyword)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def generate_qrcode(reg_no: str):
        """
        `generate_qr_code` takes a registration number of a specimen
        as a string and returns a QR code image containing the
        herbarium label
        :param reg_no: The registration number of the specimen
        :type reg_no: str
        :return: A QR code image
        """
        try:
            return SpecimenService.generate_qr_code(reg_no)
        except SpecimenExceptionRegNo as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def search_specimens_by_keyword(keyword: str):
        """
        It takes a string as an argument, and returns a list of Specimen objects
        :param keyword: str
        :type keyword: str
        :return: A list of specimens that match the keyword.
        """
        try:
            return SpecimenService.search_specimens_by_keyword(keyword)
        except SearchResultsNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
