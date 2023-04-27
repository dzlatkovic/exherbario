from app.db import SessionLocal
from app.taxonomy.repository import TaxonomyRepository
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank


class TaxonomyService:
    @staticmethod
    def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            with SessionLocal() as db:
                repository = TaxonomyRepository(db)
                return repository.create_taxon(taxon_data, taxon_rank)
        except Exception as error:
            raise error
