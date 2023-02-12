from app.storage.models import Storage
from app.storage.exceptions import StorageNotFoundException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session


class StorageRepository:

    def __init__(self, db: Session):
        self.db = db

    def create_storage(self, room: str, shelf: str, box: str):
        try:
            storage = Storage(room, shelf, box)
            self.db.add(storage)
            self.db.commit()
            self.db.refresh(storage)
            return storage
        except IntegrityError as e:
            raise e
        except Exception as e:
            raise e

    def read_all(self):
        return self.db.query(Storage).all()

    def read_storage_by_id(self, storage_id: str):
        storage = self.db.query(Storage).filter(Storage.storage_id == storage_id).first()
        if storage is None:
            raise StorageNotFoundException(f"Box with the provided ID: {storage_id} not found.", 400)
        return storage

    def delete_storage(self, storage_id: str):
        try:
            storage = self.db.query(Storage).filter(Storage.storage_id == storage_id).first()
            if storage is None:
                raise StorageNotFoundException(f"Box with provided ID: {storage_id} not found.", 400)
            self.db.delete(storage)
            self.db.commit()
            return True
        except Exception as e:
            raise e

    def read_storage_by_box(self, box: str):
        return self.db.query(Storage).filter(Storage.box == box).first()
