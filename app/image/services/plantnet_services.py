import json

from app.db import SessionLocal
from app.image.exceptions.plantnet_exceptions import PlantNetRequestFailedException
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
            with open(image_path, 'rb') as f:
                image_data = f.read()
            data = {
                'organs': [organs.value]
            }
            files = [
                ('images', (image_path, image_data))
            ]
            req = requests.Request('POST', url=PLANT_NET_API_ENDPOINT, files=files, data=data)
            prepared = req.prepare()
            s = requests.Session()
            response = s.send(prepared)
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


