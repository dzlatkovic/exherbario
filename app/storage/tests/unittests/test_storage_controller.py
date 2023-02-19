import pytest
from fastapi import HTTPException

from app.storage.exceptions import StorageNotFoundException, StorageExceptionBox
from app.tests import TestClass, TestingSessionLocal
from app.storage.controller import StorageController


class TestStorageController(TestClass):
    """This class tests the StorageController class"""

    @staticmethod
    def test_create_new_storage_box_success():
        """
        Test case for creating a new storage box successfully
        """
        storage = StorageController.create_new_storage("Room A", "Shelf 1", "Box 1")
        assert storage.room == "Room A"
        assert storage.shelf == "Shelf 1"
        assert storage.box == "Box 1"

    @staticmethod
    def test_create_new_storage_box_failure():
        """
        Test case for attempting to create a new storage box that already exists
        """
        with pytest.raises(HTTPException):
            StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
            StorageController.create_new_storage("Room A", "Shelf 1", "Box 1")

    @staticmethod
    def test_get_all_storage_boxes_success():
        """
        Test case for retrieving all storage boxes successfully
        """
        StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
        storage_boxes = StorageController.get_all()
        assert len(storage_boxes) > 0

    @staticmethod
    def test_get_storage_box_by_id_success():
        """
        Test case for retrieving a storage box by ID successfully
        """
        box = StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
        box_id = box.storage_id
        storage_box = StorageController.get_storage_by_id(box_id)
        assert storage_box.storage_id == box_id

    @staticmethod
    def test_get_storage_box_by_id_failure():
        """
        Test case for attempting to retrieve a non-existent storage box by ID
        """
        StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
        with pytest.raises(HTTPException):
            StorageController.get_storage_by_id("100")

    @staticmethod
    def test_delete_storage_box_by_id_success():
        """
        Test case for deleting a storage box by ID successfully
        """
        box = StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
        box_id = box.storage_id
        response = StorageController.delete_storage_by_id(box_id)
        assert response.status_code == 200

    @staticmethod
    def test_delete_storage_box_by_id_failure():
        """
        Test case for attempting to delete a non-existent storage box by ID
        """
        box = StorageController.create_new_storage("Room B", "Shelf 2", "Box 1")
        with pytest.raises(HTTPException):
            StorageController.delete_storage_by_id("100")

