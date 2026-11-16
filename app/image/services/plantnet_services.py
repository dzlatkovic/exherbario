import json
from typing import List, Dict

from app.db import SessionLocal
from app.image.exceptions.plantnet_exceptions import PlantNetRequestFailedException, \
    MissingPlantNetIdentificationException
from app.image.repository import PlantNetRepository
import requests
from app.config import settings
from app.image.schemas import Organs, PlantNetResultSchemaIn
from app.image.services import ImageService

PROJECT = "all"
API_KEY = settings.PLANTNET_API_KEY
PLANT_NET_API_ENDPOINT = f"https://my-api.plantnet.org/v2/identify/{PROJECT}?api-key={API_KEY}"


class PlantNetService:
    @staticmethod
    def plantnet_identify(image_id: str, organs: Organs):
        try:
            image = ImageService.get_image_by_id(image_id)
            image_path = image.file_path
            with ImageService.storage_path(image_path).open('rb') as f:
                image_data = f.read()
            data = {
                'organs': [organs.value]
            }
            files = [
                ('images', (image_path, image_data))
            ]
            req = requests.Request('POST', url=PLANT_NET_API_ENDPOINT, files=files, data=data)
            prepared = req.prepare()
            with requests.Session() as session:
                response = session.send(prepared, timeout=(5, 30))
            if response.status_code != 200:
                raise PlantNetRequestFailedException(code=response.status_code, message=response.text)
            json_result = json.loads(response.text)
            return PlantNetResultSchemaIn(
                image_id=image.image_id,
                best_match=json_result["bestMatch"],
                gbif_id=json_result["results"][0]["gbif"]["id"],
                score=json_result["results"][0]["score"]
            )

        except Exception as error:
            raise error

    @staticmethod
    def save_plantnet_identification(image_id: str, organs: Organs):
        plantnet_result = PlantNetService.plantnet_identify(image_id, organs)
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                return repository.save_plantnet_identification(plantnet_result)
        except Exception as error:
            raise error

    @staticmethod
    def get_id_result_by_id(result_id: str):
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                return repository.get_id_result_by_id(result_id)
        except Exception as error:
            raise error

    @staticmethod
    def delete_plantnet_identification(result_id: str):
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                return repository.delete_plantnet_identification(result_id)
        except Exception as error:
            raise error

    @staticmethod
    def get_plantnet_result_for_image(image_id: str):
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                plantnet_results = repository.get_plantnet_result_for_image(image_id)
                if not plantnet_results:
                    raise MissingPlantNetIdentificationException(code=400,
                                                                 message="No results found.")
                return plantnet_results
        except Exception as error:
            raise error

    @staticmethod
    def get_plantnet_result_for_specimen(specimen_id: str):
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                plantnet_results = repository.get_plantnet_result_for_specimen(specimen_id)
                if not plantnet_results:
                    raise MissingPlantNetIdentificationException(code=400,
                                                                 message="No results found.")
                return plantnet_results
        except Exception as error:
            raise error

    @staticmethod
    def get_plantnet_results_with_mismatched_taxonomy() -> List[Dict[str, str]]:
        """
        Retrieves all PlantNet results for specimens whose GBIF key in the taxonomy table
        does not match the GBIF ID in the PlantNet results, and joins the results with
        other relevant tables.

        :return: A list of dictionaries containing the relevant fields from the database.
        """
        try:
            with SessionLocal() as db:
                repository = PlantNetRepository(db)
                results = repository.get_plantnet_results_with_mismatched_taxonomy()
                return results

        except Exception as error:
            raise error
