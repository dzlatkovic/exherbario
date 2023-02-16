from app.specimen.services import SpecimenService
from app.specimen.exceptions import SpecimenExceptionRegNo, SpecimenNotFoundException

from fastapi import HTTPException, Response


class SpecimenController:

    @staticmethod
    def create_new_specimen(reg_no: str, collection_date: str, reg_date: str,
                            family: str, genus: str, species: str, subnomen: str,
                            field_loc_id: str, storage_id: str, photos_id: str,
                            collected_by: str, verified_by: str):
        try:
            return SpecimenService.create_new_specimen(reg_no, collection_date, reg_date,
                                                       family, genus, species, subnomen,
                                                       field_loc_id, storage_id, photos_id,
                                                       collected_by, verified_by)
        except ValueError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except SpecimenExceptionRegNo as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_specimen_by_id(specimen_id: str):
        try:
            return SpecimenService.read_specimen_by_id(specimen_id)
        except SpecimenNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_specimen_by_id(specimen_id: str):
        try:
            SpecimenService.delete_specimen_by_id(specimen_id)
            return Response(content=f"Specimen with ID: {specimen_id} deleted.", status_code=200)
        except SpecimenNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
