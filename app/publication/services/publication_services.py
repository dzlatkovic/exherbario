"""
This module defines a PublicationService class, which provides an
interface to the PublicationRepository for creating,
reading, and deleting Publication objects.
"""


from app.publication.models import Publication
from app.db import SessionLocal
from app.publication.repository import PublicationRepository
from app.publication.exceptions import PublicationExceptionDoi, PublicationNotFoundException
from app.publication.schemas import PublicationSchemaUpdate
from app.publication import crossref
from app.publication.crossref import FIELDS, normalize_doi
from app.external.lookups import parse_retrieved_at, peek, record_import


class PublicationService:
    """
    Provides an interface to the PublicationRepository for creating,
    reading, and deleting Publication objects.
    """
    @staticmethod
    def _record_source(db, publication, source, actor_id):
        """Log which saved values match the Crossref record the curator looked up, and which were edited."""
        saved = {"doi": publication.doi, "title": publication.title, "journal": publication.journal,
                 "year": publication.year.strftime("%Y") if publication.year else None,
                 "abstract": publication.abstract}
        doi = normalize_doi(source.external_id)
        proposal = peek("crossref", f"work:{doi}")
        proposed = crossref.fields_from(proposal.data, doi) if proposal is not None and proposal.found else {}
        accepted = [name for name in FIELDS if proposed.get(name) is not None and (
            normalize_doi(saved[name]) == proposed[name] if name == "doi" else saved[name] == proposed[name])]
        record_import(db, provider="crossref", external_id=doi, record_type="publication",
                      record_id=publication.pub_id,
                      fields={"accepted": accepted, "edited": [name for name in FIELDS if name not in accepted]},
                      confirmed_by=actor_id,
                      retrieved_at=proposal.retrieved_at if proposal else parse_retrieved_at(source.retrieved_at))
        db.commit()

    @staticmethod
    def existing_dois(repository) -> dict:
        """Normalized DOIs already in the bibliography, so `10.1/X` and `https://doi.org/10.1/x` count as one."""
        found = {}
        for publication in repository.read_all():
            try:
                found.setdefault(normalize_doi(publication.doi), publication.pub_id)
            except ValueError:
                found.setdefault(publication.doi.strip().lower(), publication.pub_id)
        return found

    @staticmethod
    def lookup_doi(doi: str):
        with SessionLocal() as db:
            existing = PublicationService.existing_dois(PublicationRepository(db))
        return crossref.lookup(doi, existing)

    @staticmethod
    def create_new_publication(doi: str, year: str, journal: str,
                               title: str, abstract: str, source=None,
                               actor_id: str | None = None) -> PublicationExceptionDoi or Publication:
        """
        Creates a new Publication object with the specified DOI, year, journal, and title
        :param doi: The DOI of the publication
        :param year: The publication year
        :param journal: The journal in which the publication was published
        :param title: The title of the publication
        :param abstract: Publication abstract
        :return: The newly created Publication object
        """
        try:
            with SessionLocal(expire_on_commit=False) as db:
                repository = PublicationRepository(db)
                try:
                    key = normalize_doi(doi)
                except ValueError:
                    key = doi.strip().lower()
                if key in PublicationService.existing_dois(repository):
                    raise PublicationExceptionDoi(message="Publication exists in the database.", code=400)
                publication = repository.create_publication(doi, year, journal, title, abstract)
                if source is not None and actor_id:
                    PublicationService._record_source(db, publication, source, actor_id)
                return publication
        except Exception as error:
            raise error

    @staticmethod
    def read_all():
        """
        Reads all Publication objects from the database
        :return: A list of Publication objects
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_all()
        except Exception as error:
            raise error

    @staticmethod
    def read_publication_by_id(pub_id: str):
        """
        Reads a Publication object with the specified ID from the database
        :param pub_id: The ID of the Publication to read
        :return: The Publication object with the specified ID
        :raises Exception: If an error occurs while reading the Publication object
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.read_publication_by_id(pub_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_publication_by_id(pub_id: str):
        """
        Deletes a Publication object with the specified ID from the database
        :param pub_id: The ID of the Publication to delete
        :return: True if the Publication was successfully deleted
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                return repository.delete_publication(pub_id)
        except Exception as error:
            raise error

    @staticmethod
    def update_publication(pub_id: str, publication: PublicationSchemaUpdate):
        """
        It takes a publication id and a publication object as
        input, and returns the updated publication object
        :param pub_id: str - the id of the publication to be updated
        :type pub_id: str
        :param publication: PublicationSchemaUpdate
        :type publication: PublicationSchemaUpdate
        :return: The updated publication.
        """
        try:
            with SessionLocal() as db:
                repository = PublicationRepository(db)
                db_publication = repository.update_publication(pub_id, publication)
            if db_publication is None:
                raise PublicationNotFoundException(message="Publication not found.",
                                                   code=400)
            return db_publication
        except Exception as error:
            raise error
