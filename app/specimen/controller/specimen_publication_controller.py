from app.specimen.exceptions import SpecimenPublicationNotFoundException
from app.specimen.services import SpecimenPublicationService
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Response


class SpecimenPublicationController:

    @staticmethod
    def create_new_specimen_publication(specimen_id: str, publication_id: str):
        try:
            return SpecimenPublicationService.create_new_specimen_publication(
                specimen_id, publication_id)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Entry already exists in the database.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_specimen_publication_by_id(specimen_publication_id: str):
        try:
            SpecimenPublicationService.delete_specimen_publication_by_id(specimen_publication_id)
            return Response(content=f"Entry with ID: {specimen_publication_id} deleted.", status_code=200)
        except SpecimenPublicationNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
