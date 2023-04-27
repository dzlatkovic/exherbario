from fastapi import APIRouter

from app.taxonomy.controller import TaxonomyController
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonomySchema, TaxonRank

taxonomy_router = APIRouter(prefix="/api/taxonomy", tags=["Taxonomy"])


@taxonomy_router.post("/create-taxon", response_model=TaxonomySchema)
def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
    return TaxonomyController.create_taxon(taxon_data, taxon_rank)
