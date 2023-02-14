from fastapi import APIRouter

from app.publication.controller import PublicationController, PublicationAuthorsController
from app.publication.schemas import (
    PublicationSchema,
    PublicationSchemaIn,
    PublicationAuthorsSchema,
    PublicationAuthorsSchemaIn
)

publication_router = APIRouter(prefix="/api/publication", tags=["Publication"])


@publication_router.post("/create-new-publication", response_model=PublicationSchema)
def create_new_course(publication: PublicationSchemaIn):
    return PublicationController.create_new_publication(doi=publication.doi, year=publication.year,
                                                        journal=publication.journal, title=publication.title)


@publication_router.get("/get-all", response_model=list[PublicationSchema])
def get_all():
    return PublicationController.get_all()


@publication_router.get("/get-publication-by-id", response_model=PublicationSchema)
def get_storage_by_id(pub_id: str):
    return PublicationController.get_publication_by_id(pub_id)


@publication_router.delete("/delete-storage")
def delete_publication_by_id(pub_id: str):
    return PublicationController.delete_publication_by_id(pub_id)


publication_authors_router = APIRouter(prefix="/api/publication_authors", tags=["Publication authors"])


@publication_authors_router.post("/create-new-publication-authors",
                                 response_model=PublicationAuthorsSchema)
def create_new_publication_authors(publication_authors: PublicationAuthorsSchemaIn):
    return PublicationAuthorsController.create_new_publication_authors(
        user_id=publication_authors.user_id,
        publication_id=publication_authors.publication_id
    )


@publication_authors_router.delete("/delete-publication-authors")
def delete_publication_by_id(publication_authors_id: str):
    return PublicationAuthorsController.delete_publication_authors_by_id(publication_authors_id)
