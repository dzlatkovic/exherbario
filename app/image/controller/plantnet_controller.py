from fastapi import HTTPException

from app.image.exceptions import ImageNotFoundException
from app.image.exceptions.plantnet_exceptions import PlantNetRequestFailedException
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
