from fastapi import HTTPException

from app.specimen.schemas import RevisionSchemaIn
from app.specimen.services import RevisionService


class RevisionController:
    @staticmethod
    def create_new_revision(revision_data: RevisionSchemaIn):
        try:
            return RevisionService.create_revision(revision_data)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
