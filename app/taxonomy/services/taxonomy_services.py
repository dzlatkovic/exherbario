from requests import RequestException
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.taxonomy.exceptions import (TaxonDoesNotExistException,
                                     TaxonAlreadyExistException,
                                     TaxonomyServiceException,
                                     GBIFServiceException)
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TAXON_DICT, TaxonRank
from pygbif import species


class TaxonomyService:
    @staticmethod
    def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                if taxon_data.parent_taxon_key is not None:
                    parent_taxon = repository.read_taxon_by_taxon_id(taxon_data.parent_taxon_key)
                    if not parent_taxon:
                        raise TaxonDoesNotExistException(
                            code=404,
                            message=f"Parent taxon with id: "
                                    f"{taxon_data.parent_taxon_key} does not exist in the database."
                        )
                return repository.create_taxon(taxon_data, taxon_rank)
        except Exception as error:
            raise error

    @staticmethod
    def read_taxon_by_gbif_key(gbif_key: str):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_gbif_key(gbif_key)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with gbif key: {gbif_key} does not exist in the database."
                    )
                return taxon
        except Exception as error:
            raise error

    @staticmethod
    def read_taxon_by_taxon_id(taxon_id: str):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_taxon_id(taxon_id)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with id: {taxon_id} does not exist in the database."
                    )
                return taxon
        except Exception as error:
            raise error

    @staticmethod
    def _fetch_taxon(gbif_key: str):
        try:
            data = species.name_usage(key=gbif_key, timeout=(5, 20))
        except RequestException as error:
            raise GBIFServiceException(message="Unable to retrieve this taxon from GBIF.", code=502) from error
        if (not isinstance(data, dict) or str(data.get("key")) != gbif_key
                or not isinstance(data.get("scientificName"), str)):
            raise GBIFServiceException(message="GBIF returned an unexpected taxon.", code=502)
        return data

    @staticmethod
    def _add_taxon(repository, data, rank, parent_id):
        details = TaxonomySchemaIn(
            taxon_name=data.get("scientificName"),
            gbif_key=str(data["key"]),
            parent_taxon_key=parent_id,
            common_name=data.get("vernacularName"),
            authority=data.get("authorship"),
        )
        return repository.add_taxon(details, rank)

    @staticmethod
    def create_taxon_from_gbif_data(gbif_key: str):
        gbif_key = str(gbif_key)
        data = TaxonomyService._fetch_taxon(gbif_key)
        rank = TAXON_DICT.get(data.get("rank"))
        if rank is None:
            raise TaxonomyServiceException(message="This GBIF rank is unsupported.", code=422)
        try:
            with SessionLocal(expire_on_commit=False) as db, db.begin():
                repo = TaxonomyRepository(db)
                if repo.read_taxon_by_gbif_key(gbif_key):
                    raise TaxonAlreadyExistException(message="This GBIF taxon already exists.", code=409)
                parent_id = None
                if rank != TaxonRank.KINGDOM:
                    parent = repo.read_taxon_by_gbif_key(str(data.get("parentKey")))
                    if parent is None:
                        raise TaxonDoesNotExistException(
                            message="The GBIF parent is missing. Import the hierarchy first.", code=404
                        )
                    parent_id = parent.taxon_id
                return TaxonomyService._add_taxon(repo, data, rank, parent_id)
        except IntegrityError as error:
            raise TaxonomyServiceException(message="The GBIF taxon could not be stored.", code=409) from error

    @staticmethod
    def build_taxonomic_tree(gbif_key: str):
        key = str(gbif_key)
        ancestors = []
        seen = set()
        try:
            with SessionLocal(expire_on_commit=False) as db, db.begin():
                repository = TaxonomyRepository(db)
                parent_id = None
                while key:
                    if key in seen:
                        raise GBIFServiceException(message="GBIF returned a cyclic taxonomy.", code=502)
                    seen.add(key)
                    existing = repository.read_taxon_by_gbif_key(key)
                    if existing is not None:
                        parent_id = existing.taxon_id
                        break
                    data = TaxonomyService._fetch_taxon(key)
                    rank = TAXON_DICT.get(data.get("rank"))
                    if rank is None and len(seen) == 1:
                        raise TaxonomyServiceException(message="This GBIF rank is unsupported.", code=422)
                    if rank is not None:
                        ancestors.append((data, rank))
                    if rank == TaxonRank.KINGDOM:
                        break
                    parent_key = data.get("parentKey")
                    if parent_key is None:
                        raise TaxonomyServiceException(message="GBIF taxonomy has no supported root.", code=422)
                    key = str(parent_key)

                created = []
                for data, rank in reversed(ancestors):
                    taxon = TaxonomyService._add_taxon(repository, data, rank, parent_id)
                    created.append(taxon)
                    parent_id = taxon.taxon_id
                return created
        except IntegrityError as error:
            raise TaxonomyServiceException(
                message="The GBIF hierarchy could not be stored. Retry if another import is in progress.", code=409
            ) from error

    @staticmethod
    def delete_taxon(taxon_id):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.read_taxon_by_taxon_id(taxon_id)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"Taxon with id: {taxon_id} does not exist in the database."
                    )
                return repository.delete_taxon(taxon_id)
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

    @staticmethod
    def get_specimens_by_taxon(taxon_name: str):
        with SessionLocal() as db:
            specimens = TaxonomyRepository(db).get_specimens_by_taxon_name(taxon_name)
            if specimens is None:
                raise TaxonDoesNotExistException(message=f"No taxon with name {taxon_name} was found.", code=404)
            return specimens
