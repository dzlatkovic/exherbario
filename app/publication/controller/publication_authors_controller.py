from app.publication.exceptions import PublicationAuthorsNotFoundException
from app.publication.services import PublicationAuthorsService
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException, Response


class PublicationAuthorsController:

    @staticmethod
    def create_new_publication_authors(user_id: str, publication_id: str):
        try:
            return PublicationAuthorsService.create_new_publication_authors(user_id, publication_id)
        except IntegrityError:
            raise HTTPException(status_code=400, detail="Entry already exists in the database.")
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))

    @staticmethod
    def delete_publication_authors_by_id(publication_authors_id: str):
        try:
            PublicationAuthorsService.delete_publication_authors_by_id(publication_authors_id)
            return Response(content=f"Entry with the provided ID: {publication_authors_id} deleted.", status_code=200)
        except PublicationAuthorsNotFoundException as e:
            raise HTTPException(status_code=e.code, detail=e.message)
        except Exception as e:
            raise HTTPException(status_code=500, detail=str(e))
