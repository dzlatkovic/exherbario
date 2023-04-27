from fastapi import HTTPException
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank
from app.taxonomy.services import TaxonomyService


class TaxonomyController:
    @staticmethod
    def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            return TaxonomyService.create_taxon(taxon_data, taxon_rank)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
