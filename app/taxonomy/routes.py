from typing import List

from fastapi import APIRouter, Depends, Query

from app.specimen.schemas import SpecimenSchema
from app.taxonomy.controller import TaxonomyController
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonomySchema, TaxonRank
from app.users.controller import JWTBearer

taxonomy_router = APIRouter(prefix="/api/taxonomy", tags=["Taxonomy"])


@taxonomy_router.post("/create-taxon", response_model=TaxonomySchema,
                      dependencies=[Depends(JWTBearer("super_user"))])
def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
    """Manually create a new taxon in the database.

    :param taxon_data: The data for the new taxon.
    :param taxon_rank: The rank of the new taxon.

    :return: The newly created taxon.
    """
    return TaxonomyController.create_taxon(taxon_data, taxon_rank)


@taxonomy_router.get("/get-taxon-by-gbif", response_model=TaxonomySchema)
def get_taxon_by_gbif(gbif_key: str):
    """Get a taxon by its GBIF key.

    :param gbif_key: The GBIF key of the taxon to retrieve.
    :return: The requested taxon.
    """
    return TaxonomyController.get_taxon_by_gbif_key(gbif_key)


@taxonomy_router.get("/get-taxon-by-id", response_model=TaxonomySchema)
def get_taxon_by_id(taxon_id: str):
    """Get a taxon by its ID.

    :param taxon_id: The ID of the taxon to retrieve.
    :return: The requested taxon.
    """
    return TaxonomyController.get_taxon_by_taxon_id(taxon_id)


@taxonomy_router.post("/create-taxon-from-gbif-data", response_model=TaxonomySchema,
                      dependencies=[Depends(JWTBearer("super_user"))])
def create_taxon_from_gbif_data(gbif_key: str):
    """Create a new taxon in the database from GBIF data using pygbif service.

    :param gbif_key: The GBIF key of the taxon to create.
    :return: The newly created taxon.
    """
    return TaxonomyController.create_taxon_from_gbif_data(gbif_key)


@taxonomy_router.get("/gbif-search", dependencies=[Depends(JWTBearer("super_user"))])
def search_gbif(q: str = Query(..., min_length=2, max_length=100)):
    """Names in the GBIF backbone for a herbarium (plants, fungi, chromists, protozoa), accepted names first.
    `taxon_id` is set when the taxon is already in this herbarium."""
    return TaxonomyController.search_gbif(q.strip())


@taxonomy_router.post("/import-from-gbif", dependencies=[Depends(JWTBearer("super_user"))])
def import_from_gbif(gbif_key: str = Query(..., pattern=r"^[0-9]{1,12}$")):
    """Add a GBIF taxon and its missing parents, and return the local taxon to link a determination to.
    A synonym is linked to its accepted name; `note` then says so."""
    return TaxonomyController.import_from_gbif(gbif_key)


@taxonomy_router.post("/build-taxonomic-tree", response_model=List[TaxonomySchema],
                      dependencies=[Depends(JWTBearer("super_user"))])
def build_taxonomic_tree(gbif_key: str):
    """Build a taxonomic tree starting from the given GBIF key.
    This function creates taxonomic entries in the database, all the way up to the Kingdom rank.

    :param gbif_key: The GBIF key to start building the tree from.
    :return: The list of newly created taxa.
    """
    return TaxonomyController.build_taxonomic_tree(gbif_key)


@taxonomy_router.delete("/delete-taxon",
                        dependencies=[Depends(JWTBearer("super_user"))])
def delete_taxon(taxon_id: str):
    """Delete a taxon by its ID.

    :param taxon_id: The ID of the taxon to delete.
    """
    return TaxonomyController.delete_taxon(taxon_id)


@taxonomy_router.get("/get-specimens-for-taxon", dependencies=[Depends(JWTBearer())], response_model=List[SpecimenSchema])
def get_specimens_by_taxon(taxon_name: str):
    """Retrieve a list of all specimens belonging to a given taxon and its child taxa.

    :param taxon_name: The name of the taxon to get specimens for.
    :return: A list of all specimens belonging to the given taxon and its child taxa.
    """
    return TaxonomyController.get_specimens_by_taxon(taxon_name)
