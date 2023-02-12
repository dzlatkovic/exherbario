from app.publication.services import PublicationService
from app.publication.exceptions import PublicationExceptionDoi, PublicationNotFoundException

from fastapi import HTTPException, Response


class PublicationController:

    @staticmethod
    def create_new_publication(doi: str, year: str, journal: str, title: str):
        try:
            return PublicationService.create_new_publication(doi, year, journal, title)
        except PublicationExceptionDoi as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def get_all():
        return PublicationService.read_all()

    @staticmethod
    def get_publication_by_id(pub_id: str):
        try:
            return PublicationService.read_publication_by_id(pub_id)
        except PublicationNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_publication_by_id(pub_id: str):
        try:
            PublicationService.delete_publication_by_id(pub_id)
            return Response(content=f"Publication with the provided ID: {pub_id} deleted.", status_code=200)
        except PublicationNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
