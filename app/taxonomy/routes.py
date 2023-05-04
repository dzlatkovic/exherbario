from typing import List

from fastapi import APIRouter

from app.specimen.schemas import SpecimenSchema
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


@taxonomy_router.post("/create-taxon-from-gbif-data", response_model=TaxonomySchema)
def create_taxon_from_gbif_data(gbif_key: str):
    return TaxonomyController.create_taxon_from_gbif_data(gbif_key)


@taxonomy_router.post("/build-taxonomic-tree", response_model=List[TaxonomySchema])
def build_taxonomic_tree(gbif_key: str):
    return TaxonomyController.build_taxonomic_tree(gbif_key)


@taxonomy_router.delete("/delete-taxon")
def delete_taxon(taxon_id: str):
    return TaxonomyController.delete_taxon(taxon_id)


@taxonomy_router.get("/get-specimens-for-taxon", response_model=List[SpecimenSchema])
def get_specimens_by_taxon(taxon_name: str):
    return TaxonomyController.get_specimens_by_taxon(taxon_name)
