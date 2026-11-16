from fastapi import HTTPException

from app.specimen.exceptions import SpecimenNotFoundException
from app.specimen.schemas import RevisionSchemaIn
from app.specimen.services import RevisionService


class RevisionController:
    @staticmethod
    def create_new_revision(revision_data: RevisionSchemaIn, revised_by: str):
        try:
            return RevisionService.create_revision(revision_data, revised_by)
        except SpecimenNotFoundException as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
