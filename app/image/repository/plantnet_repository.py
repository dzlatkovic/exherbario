from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.image.exceptions import MissingPlantNetIdentificationException
from app.image.models import PlantNetResult, Image
from app.image.schemas import PlantNetResultSchemaIn
from app.specimen.models import Specimen
from app.taxonomy.models import Taxonomy
from app.users.models import User


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

    def get_id_result_by_id(self, result_id: str):
        result = self.db.query(PlantNetResult).filter(PlantNetResult.result_id == result_id).first()
        if result is None:
            raise MissingPlantNetIdentificationException(f"Result with provided ID: "
                                                         f"{result_id} not found.", 404)
        return result

    def delete_plantnet_identification(self, result_id: str):
        try:
            image_db = self.get_id_result_by_id(result_id)
            self.db.delete(image_db)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def get_plantnet_result_for_image(self, image_id: str):
        try:
            return self.db.query(PlantNetResult).filter_by(image_id=image_id).order_by(
                desc(PlantNetResult.score)).all()
        except Exception as error:
            raise error

    def get_plantnet_result_for_specimen(self, specimen_id: str):
        try:
            return self.db.query(PlantNetResult).join(Image).filter(
                Image.specimen_id == specimen_id).order_by(
                desc(PlantNetResult.score)).all()
        except Exception as error:
            raise error

    def get_plantnet_results_with_mismatched_taxonomy(self):
        """
        Retrieves all PlantNet results for specimens whose GBIF key in the taxonomy table
        does not match the GBIF ID in the PlantNet results, and joins the results with
        other relevant tables.

        :return: A list of dictionaries containing the relevant fields from the database.
        """
        query = self.db.query(Specimen.reg_no, Specimen.subnomen, Taxonomy.gbif_key, PlantNetResult.best_match,
                              PlantNetResult.gbif_id, PlantNetResult.score, User.name, User.surname) \
            .join(Taxonomy, Specimen.taxon_id == Taxonomy.taxon_id) \
            .join(User, Specimen.verified_by == User.user_id) \
            .join(Image, Specimen.specimen_id == Image.specimen_id) \
            .join(PlantNetResult, Image.image_id == PlantNetResult.image_id) \
            .filter(Taxonomy.gbif_key != PlantNetResult.gbif_id)

        results = []
        for row in query.all():
            results.append({
                "reg_no": row[0],
                "subnomen": row[1],
                "gbif_key": row[2],
                "best_match_from_plantnet": row[3],
                "gbif_id_plantnet": row[4],
                "plantnet_score": row[5],
                "verified_by_name": row[6],
                "verified_by_surname": row[7]
            })
        return results
