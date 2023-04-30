from fastapi import HTTPException, Response
from starlette.responses import JSONResponse

from app.image.exceptions import ImageNotFoundException
from app.image.exceptions.plantnet_exceptions import (PlantNetRequestFailedException,
                                                      MissingPlantNetIdentificationException)
from app.image.schemas import Organs
from app.image.services import PlantNetService


class PlantNetController:
    @staticmethod
    def save_plantnet_identification(image_id: str, organs: Organs):
        try:
            return PlantNetService.save_plantnet_identification(image_id, organs)
        except (ImageNotFoundException,
                PlantNetRequestFailedException) as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_id_result_by_id(result_id: str):
        try:
            return PlantNetService.get_id_result_by_id(result_id)
        except MissingPlantNetIdentificationException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def delete_plantnet_identification(result_id: str):
        try:
            PlantNetService.delete_plantnet_identification(result_id)
            return Response(content=f"Identification was successfully deleted.",
                            status_code=200)
        except MissingPlantNetIdentificationException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_plantnet_result_for_image(image_id: str):
        try:
            return PlantNetService.get_plantnet_result_for_image(image_id)
        except MissingPlantNetIdentificationException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_plantnet_result_for_specimen(specimen_id: str):
        try:
            return PlantNetService.get_plantnet_result_for_specimen(specimen_id)
        except MissingPlantNetIdentificationException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_plantnet_results_with_mismatched_taxonomy():
        """
        Retrieves all PlantNet results for specimens whose GBIF key in the taxonomy table
        does not match the GBIF ID in the PlantNet results, and joins the results with
        other relevant tables.

        :return: A JSON response containing a list of dictionaries with the relevant
        fields from the database.
        """
        try:
            results = PlantNetService.get_plantnet_results_with_mismatched_taxonomy()
            return JSONResponse(content=results)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
