from sqlalchemy.orm import Session

from app.image.models import PlantNetResult
from app.image.schemas import PlantNetResultSchemaIn


class PlantNetRepository:

    def __init__(self, db: Session):
        self.db = db

    def save_plantnet_identification(self, plantnet_result: PlantNetResultSchemaIn):
        try:
            db_plantnet_result = PlantNetResult(
                                       image_id=plantnet_result.image_id,
                                       best_match=plantnet_result.best_match,
                                       gbif_id=plantnet_result.gbif_id,
                                       score=plantnet_result.score)
            self.db.add(db_plantnet_result)
            self.db.commit()
            self.db.refresh(db_plantnet_result)
            return db_plantnet_result
        except Exception as error:
            raise error
