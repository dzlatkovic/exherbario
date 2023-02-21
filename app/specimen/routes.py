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
    """Create a new specimen in the database."""
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
    > Get a specimen by its id
    :param specimen_id: The ID of the specimen you want to get
    :type specimen_id: str
    :return: A specimen object
    """
    return SpecimenController.get_specimen_by_id(specimen_id)


@specimen_router.delete("/delete-specimen", dependencies=[Depends(JWTBearer("super_user"))])
def delete_specimen_by_id(specimen_id: str):
    """
    Delete a specimen by its id
    :param specimen_id: str
    :type specimen_id: str
    :return: The return value is a tuple of the form (status, message)
    """
    return SpecimenController.delete_specimen_by_id(specimen_id)


@specimen_router.get("/get-specimen-per-year")
def get_specimen_per_year():
    """
    This function returns a list of tuples containing the number of specimens collected per year
    :return: A list of tuples containing the year and the number of specimens for that year.
    """
    return SpecimenController.get_specimens_per_year()


@specimen_router.get("/get-specimen-per-user")
def get_specimen_per_user():
    """
    This function returns a list of all specimens in the database,
    with the number of specimens per user
    :return: A list of tuples containing the user's username and the number of specimens they have.
    """
    return SpecimenController.get_specimens_per_user()


@specimen_router.get("/get-specimen-per-region")
def get_specimen_per_region():
    """
    This function returns a list of dictionaries, each dictionary containing
    the name of a region and the number of specimens in that region
    :return: A list of tuples containing the region name and the number of specimens in that region.
    """
    return SpecimenController.get_specimens_per_region()


@specimen_router.get("/count-specimen")
def count_specimen():
    """
    > Counts the number of specimens in the database
    :return: The number of specimens in the database.
    """
    return SpecimenController.count_specimens()


@specimen_router.get("/get-gps")
def get_gps_for_genus(genus: str):
    """
    This function returns a list of GPS coordinates for a given genus
    :param genus: The genus of the plant you want to get GPS coordinates for
    :type genus: str
    :return: A list of GPS coordinates for a given genus.
    """
    return SpecimenController.get_gps_for_genus(genus)


@specimen_router.get("/get-last-specimens", response_model=list[SpecimenSchema])
def get_last_specimens():
    """
    This function returns the last specimens added to the database
    :return: A list of the last 10 specimens added to the database.
    """
    return SpecimenController.get_last_specimens()


@specimen_router.get("/get-herbarium-label")
def get_herbarium_label(reg_no):
    """
    This function returns the herbarium label for a given registration number
    :param reg_no: The registration number of the specimen
    :return: A list of all the herbarium labels.
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


specimen_publication_router = APIRouter(prefix="/api/specimen_publication",
                                        tags=["Specimen publication"])


@specimen_publication_router.post("/create-new-specimen_publication",
                                  response_model=SpecimenPublicationSchema,
                                  dependencies=[Depends(JWTBearer("super_user"))])
def create_new_specimen_publication(specimen_publication: SpecimenPublicationSchemaIn):
    """
    `create_new_specimen_publication` creates a new specimen publication
    :param specimen_publication: SpecimenPublicationSchemaIn
    :type specimen_publication: SpecimenPublicationSchemaIn
    :return: The newly created specimen publication.
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
    :type specimen_publication_id: str
    :return: A list of specimen publications
    """
    return SpecimenPublicationController.delete_specimen_publication_by_id(specimen_publication_id)
