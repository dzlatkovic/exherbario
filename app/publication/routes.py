"""Publication Router module.

This module contains the API routers related to the Publication entity.
"""


from fastapi import APIRouter, Depends

from app.publication.controller import PublicationController, PublicationAuthorsController
from app.publication.schemas import (
    PublicationSchema,
    PublicationSchemaIn,
    PublicationAuthorsSchema,
    PublicationAuthorsSchemaIn
)
from app.users.controller import JWTBearer

publication_router = APIRouter(prefix="/api/publication", tags=["Publication"])


@publication_router.post("/create-new-publication", response_model=PublicationSchema,
                         dependencies=[Depends(JWTBearer("super_user"))])
def create_new_publication(publication: PublicationSchemaIn):
    """Create a new publication record.
    :param publication: The publication information to create
    :type publication: PublicationSchemaIn
    :return: The created publication record
    :rtype: PublicationSchema
    """
    return PublicationController.create_new_publication(doi=publication.doi,
                                                        year=publication.year,
                                                        journal=publication.journal,
                                                        title=publication.title)


@publication_router.get("/get-all", response_model=list[PublicationSchema])
def get_all():
    """Get all publication records
    :return: A list of all publication records.
    :rtype: list[PublicationSchema]
    """
    return PublicationController.get_all()


@publication_router.get("/get-publication-by-id", response_model=PublicationSchema)
def get_publication_by_id(pub_id: str):
    """Get a publication record by ID
    :param pub_id: The ID of the publication record to retrieve
    :type pub_id: str
    :return: The publication record with the specified ID
    :rtype: PublicationSchema
    """
    return PublicationController.get_publication_by_id(pub_id)


@publication_router.delete("/delete-publication",
                           dependencies=[Depends(JWTBearer("super_user"))])
def delete_publication_by_id(pub_id: str):
    """Delete a publication record by ID
    :param pub_id: The ID of the publication record to delete
    :type pub_id: str
    """
    return PublicationController.delete_publication_by_id(pub_id)


publication_authors_router = APIRouter(prefix="/api/publication_authors",
                                       tags=["Publication authors"])


@publication_authors_router.post("/create-new-publication-authors",
                                 response_model=PublicationAuthorsSchema,
                                 dependencies=[Depends(JWTBearer("super_user"))])
def create_new_publication_authors(publication_authors: PublicationAuthorsSchemaIn):
    """Create a new publication author record
    :param publication_authors: The publication author information to create
    :type publication_authors: PublicationAuthorsSchemaIn
    :return: The created publication author record
    :rtype: PublicationAuthorsSchema
    """
    return PublicationAuthorsController.create_new_publication_authors(
        user_id=publication_authors.user_id,
        publication_id=publication_authors.publication_id
    )


@publication_authors_router.delete("/delete-publication-authors",
                                   dependencies=[Depends(JWTBearer("super_user"))])
def delete_publication_authors_by_id(publication_authors_id: str):
    """Delete a publication author record by ID
    :param publication_authors_id: The ID of the publication author record to delete
    :type publication_authors_id: str
    """
    return PublicationAuthorsController.delete_publication_authors_by_id(publication_authors_id)


@publication_authors_router.get("/get-publication-report")
def get_publication_report():
    """
    This function returns a list of dictionaries, each dictionary
    containing the publication title, the authors,
    and the species used in the study
    :return: A list of dictionaries.
    """
    return PublicationAuthorsController.get_publication_report()
