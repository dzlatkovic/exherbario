from app.db import SessionLocal
from app.taxonomy.exceptions import TaxonDoesNotExistException
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank


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
