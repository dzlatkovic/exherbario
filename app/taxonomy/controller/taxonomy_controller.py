from fastapi import HTTPException, Response
from sqlalchemy.exc import IntegrityError

from app.taxonomy.exceptions import (TaxonDoesNotExistException,
                                     TaxonAlreadyExistException,
                                     GBIFServiceException,
                                     TaxonomyServiceException)
from app.taxonomy.schemas import TaxonomySchemaIn, TaxonRank
from app.taxonomy.services import TaxonomyService


class TaxonomyController:
    @staticmethod
    def create_taxon(taxon_data: TaxonomySchemaIn, taxon_rank: TaxonRank):
        try:
            return TaxonomyService.create_taxon(taxon_data, taxon_rank)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except TaxonDoesNotExistException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_taxon_by_gbif_key(gbif_key: str):
        try:
            return TaxonomyService.read_taxon_by_gbif_key(gbif_key)
        except TaxonDoesNotExistException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_taxon_by_taxon_id(taxon_id: str):
        try:
            return TaxonomyService.read_taxon_by_taxon_id(taxon_id)
        except TaxonDoesNotExistException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def create_taxon_from_gbif_data(gbif_key: str):
        try:
            return TaxonomyService.create_taxon_from_gbif_data(gbif_key)
        except (TaxonDoesNotExistException,
                TaxonAlreadyExistException,
                GBIFServiceException,
                TaxonomyServiceException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def build_taxonomic_tree(gbif_key: str):
        try:
            return TaxonomyService.build_taxonomic_tree(gbif_key)
        except (TaxonDoesNotExistException,
                TaxonAlreadyExistException,
                GBIFServiceException,
                TaxonomyServiceException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_taxon(taxon_id: str):
        try:
            TaxonomyService.delete_taxon(taxon_id)
            return Response(content=f"Taxon with ID: {taxon_id} deleted.", status_code=200)
        except TaxonDoesNotExistException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except IntegrityError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_specimens_by_taxon(taxon_name: str):
        try:
            return TaxonomyService.get_specimens_by_taxon(taxon_name)
        except TaxonDoesNotExistException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
