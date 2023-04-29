"""Specimen Router module.

This module contains the API routers related to the Specimen and SpecimenPublication entity.
"""


from fastapi import APIRouter, Depends
from starlette.responses import HTMLResponse

from app.specimen.controller import SpecimenController, SpecimenPublicationController
from app.specimen.schemas import SpecimenSchema, SpecimenSchemaIn, SpecimenSchemaUpdate
from app.specimen.schemas import SpecimenPublicationSchema, SpecimenPublicationSchemaIn
from app.users.controller import JWTBearer

specimen_router = APIRouter(prefix="/api/specimen", tags=["Specimen"])


@specimen_router.post("/create-new-specimen", response_model=SpecimenSchema,
                      dependencies=[Depends(JWTBearer("super_user"))])
def create_new_specimen(specimen: SpecimenSchemaIn):
    """
    Create a new specimen in the database using the information
    provided in the SpecimenSchemaIn object.

    :param specimen: A SpecimenSchemaIn object containing the details of the new specimen.
    :type specimen: SpecimenSchemaIn
    :return: The newly created specimen object.
    """
    return SpecimenController.create_new_specimen(specimen)


@specimen_router.get("/get-specimen-by-id", response_model=SpecimenSchema)
def get_specimen_by_id(specimen_id: str):
    """
    Retrieve a specimen from the database by its ID.

    :param specimen_id: ID of the specimen to retrieve
    :type specimen_id: str
    return SpecimenController.get_specimen_by_id(specimen_id)
    """
    return SpecimenController.get_specimen_by_id(specimen_id)


@specimen_router.delete("/delete-specimen", dependencies=[Depends(JWTBearer("super_user"))])
def delete_specimen_by_id(specimen_id: str):
    """
    Delete a specimen by its id
    :param specimen_id: str
    :type specimen_id: str
    """
    return SpecimenController.delete_specimen_by_id(specimen_id)


@specimen_router.get("/get-specimen-per-year")
def get_specimen_per_year():
    """
    This function returns a list of dicts containing the number of specimens collected per year
    :return: A list of dicts containing the year and the number of specimens for that year.
    """
    return SpecimenController.get_specimens_per_year()


@specimen_router.get("/get-specimen-per-user")
def get_specimen_per_user():
    """
    It returns a dictionary of the form {'name surname': number of
    specimens collected by that user}

    :return: A dictionary with the name and surname of the user as the
    key and the number of specimens collected by that
    user as the value.
    """
    return SpecimenController.get_specimens_per_user()


@specimen_router.get("/get-specimen-per-region")
def get_specimen_per_region():
    """
    This function returns a dictionary containing
    the name of a region and the number of specimens
    collected in that region
    :return: A dictionary containing the region name and the number of specimens
    collected in that region.
    """
    return SpecimenController.get_specimens_per_region()


@specimen_router.get("/get-gps")
def get_gps_for_search_results(keyword: str):
    """
    Retrieve GPS locations for search results based on a keyword.

    This function retrieves GPS locations for search results
    that match the provided keyword. The keyword can be any
    part of the subnomen.

    :param keyword: A string representing the keyword used for searching.
    :type keyword: str
    :return: A dictionary with specimen registration numbers as keys and GPS locations as values.
    :rtype: dict
    :raises: SearchResultsNotFoundException if no search results are found.
    """
    return SpecimenController.get_gps_for_search_result(keyword)


@specimen_router.get("/visualize-gps")
def visualize_gps(keyword: str) -> HTMLResponse:
    """
    Generate a map visualization of the GPS coordinates for specimens that match the given keyword.

    :param keyword: The search keyword used to find matching specimens.
    :type keyword: str

    :return: The HTML content representing the generated map visualization.
    :rtype: HTMLResponse

    :raises HTTPException: If an error occurs while generating the map visualization.
    """
    return SpecimenController.visualize_gps(keyword)


@specimen_router.get("/get-last-specimens", response_model=list[SpecimenSchema])
def get_last_specimens():
    """
    This function returns the last 10 specimens added to the database
    """
    return SpecimenController.get_last_specimens()


@specimen_router.get("/get-herbarium-label")
def get_herbarium_label(reg_no):
    """
    Retrieve the herbarium label for a given specimen registration number.

    :param reg_no: registration number of the specimen to retrieve the herbarium label for.
    :type reg_no: str
    :return: A dictionary representing the herbarium label for the specimen
    """
    return SpecimenController.get_herbarium_label(reg_no)


@specimen_router.put("/update-specimen", response_model=SpecimenSchema,
                     dependencies=[Depends(JWTBearer("super_user"))])
def update_specimen(specimen_id: str, specimen: SpecimenSchemaUpdate):
    """
    `Update a specimen.`
    :param specimen_id: str
    :type specimen_id: str
    :param specimen: SpecimenSchemaUpdate
    :type specimen: SpecimenSchemaUpdate
    :return: The updated specimen
    """
    return SpecimenController.update_specimen(specimen_id, specimen)


@specimen_router.get("/filter-by-date")
def get_specimens_by_date_range(start_date: str, end_date: str):
    """
    Returns a list of specimens that were collected between the specified start and end dates
    :param start_date: The start date of the date range in the format 'YYYY-MM-DD'.
    :param end_date: The start date of the date range in the format 'YYYY-MM-DD'.
    :return: List[Specimen]
    """
    return SpecimenController.get_specimens_by_date_range(start_date, end_date)


@specimen_router.get("/get-specimens-by-distance")
def get_specimens_by_distance(keyword: str):
    """
    Get specimens by distance from a given keyword.

    :param keyword: The keyword to search for in the subnomen of species.
    :type keyword: str

    :return: A list of dictionaries representing the specimens, sorted by distance.
    :rtype: List[Dict[str, Union[str, int]]]

    :raises HTTPException: If any error occurs during processing.
    """
    return SpecimenController.get_specimens_by_distance(keyword)


@specimen_router.get("/generate_qr_code")
def generate_qr_code(reg_no: str):
    """
    `generate_qr_code` takes a registration number of the specimen
    as a string and returns a QR code image containing the
    herbarium label
    :param reg_no: The registration number of the specimen
    :type reg_no: str
    :return: A QR code image
    """
    return SpecimenController.generate_qrcode(reg_no)


@specimen_router.get("/search-specimens-by-keyword", response_model=list[SpecimenSchema])
def search_specimens_by_keyword(keyword: str):
    """
    Search for specimens by keyword
    :param keyword: str
    :type keyword: str
    :return: A list of Specimen objects
    """
    return SpecimenController.search_specimens_by_keyword(keyword)


specimen_publication_router = APIRouter(prefix="/api/specimen_publication",
                                        tags=["Specimen publication"])


@specimen_publication_router.post("/create-new-specimen_publication",
                                  response_model=SpecimenPublicationSchema,
                                  dependencies=[Depends(JWTBearer("super_user"))])
def create_new_specimen_publication(specimen_publication: SpecimenPublicationSchemaIn):
    """
    create_new_specimen_publication function creates a new mapping
    between specimens and publications, indicating which specimens
    were mentioned in which article.

    :param specimen_publication: A SpecimenPublicationSchemaIn object containing the
    relevant information for the new mapping
    :type specimen_publication: SpecimenPublicationSchemaIn
    :return: A new specimen publication mapping.
    """
    return SpecimenPublicationController.create_new_specimen_publication(
        specimen_id=specimen_publication.specimen_id,
        publication_id=specimen_publication.publication_id
    )


@specimen_publication_router.delete("/delete-specimen_publication",
                                    dependencies=[Depends(JWTBearer("super_user"))])
def delete_specimen_publication_by_id(specimen_publication_id: str):
    """
    Delete a specimen publication by its id

    :param specimen_publication_id: str
    """
    return SpecimenPublicationController.delete_specimen_publication_by_id(specimen_publication_id)
