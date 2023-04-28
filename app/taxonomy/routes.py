from fastapi import APIRouter

from app.taxonomy.controller import TaxonomyController
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonomySchema, TaxonRank

taxonomy_router = APIRouter(prefix="/api/taxonomy", tags=["Taxonomy"])


@taxonomy_router.post("/create-taxon", response_model=TaxonomySchema)
def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
    return TaxonomyController.create_taxon(taxon_data, taxon_rank)


@taxonomy_router.get("/get-taxon-by-gbif", response_model=TaxonomySchema)
def get_taxon_by_gbif(gbif_key: str):
    return TaxonomyController.get_taxon_by_gbif_key(gbif_key)


@taxonomy_router.get("/get-taxon-by-id", response_model=TaxonomySchema)
def get_taxon_by_id(taxon_id: str):
    return TaxonomyController.get_taxon_by_taxon_id(taxon_id)
