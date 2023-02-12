from app.photos.models import Photos
from app.photos.exceptions import PhotosNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class PhotosRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_photos(self, field_photo: str, specimen_photo: str):
        try:
            photos = Photos(field_photo, specimen_photo)
            self.db.add(photos)
            self.db.commit()
            self.db.refresh(photos)
            return photos
        except IntegrityError as e:
            raise e
        except Exception as e:
            raise e

    def read_all_photos(self):
        courses = self.db.query(Photos).all()
        return courses

    def read_photos_by_id(self, photos_id: str):
        photos = self.db.query(Photos).filter(Photos.photos_id == photos_id).first()
        if photos is None:
            raise PhotosNotFoundException(f"Photos with provided ID: {photos_id} not found.", 400)
        return photos

    def delete_photos(self, photos_id: str):
        try:
            photos = self.db.query(Photos).filter(Photos.photos_id == photos_id).first()
            if photos is None:
                raise PhotosNotFoundException(f"Photos with provided ID: {photos_id} not found.", 400)
            self.db.delete(photos)
            self.db.commit()
            return True
        except Exception as e:
            raise e
