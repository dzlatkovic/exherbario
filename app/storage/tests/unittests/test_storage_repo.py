import pytest
from sqlalchemy.exc import IntegrityError

from app.storage.exceptions import StorageNotFoundException
from app.tests import TestClass, TestingSessionLocal
from app.storage.repository import StorageRepository


class TestStorageRepo(TestClass):
    """
    This class tests the StorageRepository class.
    """
    def create_storages_for_methods(self):
        """
        It creates two new storage boxes.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            storage_repository.create_storage("room1", "shelf1", "box1")
            storage_repository.create_storage("room2", "shelf2", "box2")

    def test_create_storage(self):
        """
        This function tests the create_storage method.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            storage = storage_repository.create_storage("room1", "shelf1", "box1")
            assert storage.room == "room1"
            assert storage.shelf == "shelf1"

    def test_read_all(self):
        """
        This function tests the read_all method.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            storages = storage_repository.read_all()
            assert len(storages) == 0
            storage_repository.create_storage("room1", "shelf1", "box1")
            storage_repository.create_storage("room2", "shelf2", "box2")
            storages = storage_repository.read_all()
            assert len(storages) == 2

    def test_read_storage_by_id(self):
        """
        This function tests the read_storage_by_id method.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            self.create_storages_for_methods()
            storage = storage_repository.read_all()[0]
            retrieved_storage = storage_repository.read_storage_by_id(storage.storage_id)
            assert storage == retrieved_storage
            with pytest.raises(StorageNotFoundException):
                storage_repository.read_storage_by_id("999")

    def test_delete_storage(self):
        """
        This function tests the delete_storage method.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            self.create_storages_for_methods()
            storages = storage_repository.read_all()
            assert len(storages) == 2
            storage_repository.delete_storage(storages[0].storage_id)
            storages = storage_repository.read_all()
            assert len(storages) == 1

    def test_read_storage_by_box(self):
        """
        This function tests the read_storage_by_box method.
        """
        with TestingSessionLocal() as db:
            storage_repository = StorageRepository(db)
            self.create_storages_for_methods()
            storage = storage_repository.read_all()[0]
            retrieved_storage = storage_repository.read_storage_by_box(storage.box)
            assert storage == retrieved_storage

    def test_create_storage_with_existing_name(self):
        """
        Create a storage with a unique name, then try to create another
        storage with the same name
        """
        with TestingSessionLocal() as db:
            repository = StorageRepository(db)
            repository.create_storage(room="Test Room", shelf="Test Shelf", box="Test Box")
            with pytest.raises(IntegrityError):
                repository.create_storage(room="Test Room", shelf="Test Shelf", box="Test Box")

    def test_read_nonexistent_storage(self):
        """
        It tests that a nonexistent storage cannot be read
        """
        with TestingSessionLocal() as db:
            repository = StorageRepository(db)
            with pytest.raises(StorageNotFoundException):
                repository.read_storage_by_id("nonexistent_id")

    def test_delete_nonexistent_storage(self):
        """
        It should raise an exception when trying to delete a nonexistent storage
        """
        with TestingSessionLocal() as db:
            repository = StorageRepository(db)
            with pytest.raises(StorageNotFoundException):
                repository.delete_storage("nonexistent_id")
