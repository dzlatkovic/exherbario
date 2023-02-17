"""
This module defines the StorageRepository class,
which provides methods for interacting with the
storage database table.
"""

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, joinedload

from app.specimen.models import Specimen
from app.storage.models import Storage
from app.storage.exceptions import StorageNotFoundException


class StorageRepository:
    """
    The StorageRepository class provides methods for interacting
    with the storage database table.
    """
    def __init__(self, db: Session):
        """Create a new StorageRepository instance
        :param db: The database session object
        """
        self.db = db

    def create_storage(self, room: str, shelf: str, box: str):
        """Create a new storage box
        :param room: The room where the box is located
        :param shelf: The shelf where the box is located
        :param box: The name of the box
        """
        try:
            storage = Storage(room, shelf, box)
            self.db.add(storage)
            self.db.commit()
            self.db.refresh(storage)
            return storage
        except IntegrityError as error:
            raise error
        except Exception as error:
            raise error

    def read_all(self):
        """Get all storage boxes."""
        return self.db.query(Storage).all()

    def read_storage_by_id(self, storage_id: str):
        """Get a storage box by ID
        :param storage_id: The ID of the storage box
        """
        storage = self.db.query(Storage).filter(Storage.storage_id == storage_id).first()
        if storage is None:
            raise StorageNotFoundException(f"Box with the provided ID: "
                                           f"{storage_id} not found.", 400)
        return storage

    def delete_storage(self, storage_id: str):
        """Delete a storage box by ID
        :param storage_id: The ID of the storage box
        """
        try:
            storage = self.db.query(Storage).filter(Storage.storage_id == storage_id).first()
            if storage is None:
                raise StorageNotFoundException(f"Box with provided ID: {storage_id} "
                                               f"not found.", 400)
            self.db.delete(storage)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def read_storage_by_box(self, box: str):
        """Get a storage box by name
        :param box: The name of the storage box.
        """
        return self.db.query(Storage).filter(Storage.box == box).first()

    def get_box_content(self, box: str):
        try:
            if not self.db.query(Storage).filter(Storage.box == box).first():
                raise StorageNotFoundException("Box not found.", 400)
            query = self.db.query(Storage, Specimen) \
                .filter(Storage.box == box) \
                .filter(Specimen.storage_id == Storage.storage_id) \
                .all()

            results = []
            for storage, specimen in query:
                data = {
                    "box": box,
                    "reg_no": specimen.reg_no,
                    "family": specimen.family,
                    "genus": specimen.genus,
                    "species": specimen.species,
                }
                results.append(data)
            return results
        except Exception as error:
            raise error
