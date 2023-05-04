from typing import List

from requests import HTTPError
from sqlalchemy.exc import IntegrityError

from app.db import SessionLocal
from app.taxonomy.exceptions import (TaxonDoesNotExistException,
                                     TaxonAlreadyExistException,
                                     TaxonomyServiceException,
                                     GBIFServiceException)
from app.taxonomy.models import Taxonomy
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank, TAXON_DICT
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
    def get_taxon_id(gbif_key):
        try:
            taxon = TaxonomyService.read_taxon_by_gbif_key(gbif_key)
            return taxon.taxon_id
        except Exception as error:
            raise error

    @staticmethod
    def create_input_schema_from_gbif_data(taxon_gbif_data):
        taxon_name = taxon_gbif_data.get("scientificName")
        gbif_key = str(taxon_gbif_data.get("key"))
        try:
            parent_taxon_key = TaxonomyService.get_taxon_id(str(taxon_gbif_data["parentKey"]))
        except TaxonDoesNotExistException:
            raise TaxonDoesNotExistException(
                code=404,
                message=f"Parent taxon with gbif key "
                        f"{taxon_gbif_data['parentKey']} does not exist in the database.")
        common_name = taxon_gbif_data.get("vernacularName")
        authority = taxon_gbif_data.get("authorship")
        return TaxonomySchemaIn(
            taxon_name=taxon_name,
            gbif_key=gbif_key,
            parent_taxon_key=parent_taxon_key,
            common_name=common_name,
            authority=authority
        )

    @staticmethod
    def is_taxon_present(gbif_key: str) -> bool:
        """
        Returns True if a taxon with the given GBIF key
        exists in the database, and False otherwise.
        :param gbif_key: A string representing the GBIF key for the taxon.
        :return: A boolean value indicating whether the taxon exists in the database.
        """
        with SessionLocal() as db:
            repository = TaxonomyRepository(db)
            taxon = repository.read_taxon_by_gbif_key(gbif_key)
            if taxon:
                return True
            return False

    @staticmethod
    def create_taxon_from_gbif_data(gbif_key):
        try:
            if TaxonomyService.is_taxon_present(gbif_key):
                raise TaxonAlreadyExistException(
                    code=400,
                    message=f"Taxon with gbif key: {gbif_key} already exists in the database."
                )
            taxon_gbif_data = species.name_usage(key=gbif_key)
            taxon_input_schema = TaxonomyService.create_input_schema_from_gbif_data(taxon_gbif_data)
            taxon_rank = TAXON_DICT[taxon_gbif_data["rank"]]
            return TaxonomyService.create_taxon(taxon_input_schema, taxon_rank)
        except (TaxonDoesNotExistException, TaxonAlreadyExistException) as error:
            raise error
        except HTTPError as error:
            raise GBIFServiceException(message="Error downloading data from GBIF.", code=400) from error
        except Exception as error:
            raise TaxonomyServiceException(message="Error creating taxon", code=400) from error

    @staticmethod
    def build_taxonomic_tree(gbif_key):
        try:
            if TaxonomyService.is_taxon_present(gbif_key):
                raise TaxonAlreadyExistException(
                    code=400,
                    message=f"Taxon with gbif key: {gbif_key} already exists in the database."
                )
            rank_keys = ["kingdomKey", "phylumKey", "orderKey", "familyKey", "genusKey", "speciesKey"]
            taxon_gbif_data = species.name_usage(key=gbif_key)
            new_taxa = []
            for rank in rank_keys:
                try:
                    new_taxon = TaxonomyService.create_taxon_from_gbif_data(taxon_gbif_data[rank])
                    new_taxa.append(new_taxon)
                except TaxonAlreadyExistException:
                    continue
                except KeyError:
                    break
            return new_taxa
        except Exception as error:
            raise error

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
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                taxon = repository.get_taxon_by_name(taxon_name)
                if not taxon:
                    raise TaxonDoesNotExistException(
                        code=404,
                        message=f"No taxon with name {taxon_name} was found."
                    )
                child_taxa = TaxonomyService.get_all_child_taxa(taxon, repository)
                taxon_ids = [taxon.taxon_id for taxon in child_taxa] + [taxon.taxon_id]
                specimens = []
                for taxon_id in taxon_ids:
                    specimens += repository.get_specimens_by_taxon_id(taxon_id)
                return specimens
        except Exception as error:
            raise error

    @staticmethod
    def get_all_child_taxa(taxon: Taxonomy, repository: TaxonomyRepository) -> List[Taxonomy]:
        """
        Recursively get all child taxa for a given taxon.
        """
        children = []
        child_taxa = repository.get_all_child_taxa_by_parent_taxon_key(taxon.taxon_id)
        if not child_taxa:
            return []
        for child in child_taxa:
            children.append(child)
            children += TaxonomyService.get_all_child_taxa(child, repository)
        return children


