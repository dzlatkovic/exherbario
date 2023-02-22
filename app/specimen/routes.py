"""Specimen Router module.

This module contains the API routers related to the Specimen and SpecimenPublication entity.
"""


from fastapi import APIRouter, Depends

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
    return SpecimenController.create_new_specimen(reg_no=specimen.reg_no,
                                                  collection_date=specimen.collection_date,
                                                  reg_date=specimen.reg_date,
                                                  family=specimen.family,
                                                  genus=specimen.genus,
                                                  species=specimen.species,
                                                  subnomen=specimen.subnomen,
                                                  field_loc_id=specimen.field_loc_id,
                                                  storage_id=specimen.storage_id,
                                                  photos_id=specimen.photos_id,
                                                  collected_by=specimen.collected_by,
                                                  verified_by=specimen.verified_by)


@specimen_router.get("/get-specimen-by-id", response_model=SpecimenSchema)
def get_storage_by_id(specimen_id: str):
    """
    Retrieve a specimen from the database by its ID.

    :param specimen_id: ID of the specimen to retrieve
    :type specimen_id: str
    return SpecimenController.get_specimen_by_id(specimen_id)
    """


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


@specimen_router.get("/count-specimen")
def count_specimen():
    """
    Count the number of unique specimens, families, genera, and species in the database.

    :return: A dictionary containing the counts of unique specimens, families,
    genera, and species in the database.
    """
    return SpecimenController.count_specimens()


@specimen_router.get("/get-gps")
def get_gps_for_genus(genus: str):
    """
    Retrieve the GPS coordinates of all specimens belonging to a given genus.

    :param genus: A string representing the genus of the specimens to retrieve.
    :type genus: str
    :return: A dictionary of the register number of each specimen and its GPS
    coordinates, in the format {reg_no: {subnomen, gps}}.
    """
    return SpecimenController.get_gps_for_genus(genus)


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


@specimen_router.get("/get-specimens-by-genus-and-distance")
def get_specimens_by_genus_and_distance(genus: str):
    """
    Returns a list of specimens for the specified genus
    sorted by distance from the Faculty of Sciences and Mathematics, Nis
    :param genus: The genus of the specimens to retrieve.
    :return: list[dict]: A list of dictionaries containing the registration
    number, subnomen, and distance of each specimen, sorted by distance from PMF Nis.
    """
    return SpecimenController.get_specimens_by_genus_and_distance(genus)


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
