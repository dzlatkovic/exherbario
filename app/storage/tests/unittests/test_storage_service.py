import pytest
from sqlalchemy.exc import IntegrityError

from app.storage.exceptions import StorageNotFoundException, StorageExceptionBox
from app.tests import TestClass, TestingSessionLocal
from app.storage.services import StorageService


class TestStorageService(TestClass):
    """This class tests the StorageService class"""
    def create_boxes(self):
        """
        It creates two new storage boxes
        """
        StorageService.create_new_storage("Room1", "Shelf1", "Box1")
        StorageService.create_new_storage("Room1", "Shelf1", "Box2")

    def test_create_new_storage(self):
        """
        Test creating a new storage box
        """
        box = StorageService.create_new_storage("Room2", "Shelf2", "Box3")
        assert box.box == "Box3"

    def test_create_existing_storage(self):
        """
        Test creating a storage box that already exists
        """
        self.create_boxes()
        with pytest.raises(StorageExceptionBox):
            StorageService.create_new_storage("Room1", "Shelf1", "Box1")

    def test_read_all(self):
        """
        Test reading all storage boxes
        """
        self.create_boxes()
        boxes = StorageService.read_all()
        assert len(boxes) == 2

    def test_read_storage_by_id(self):
        """
        Test reading a storage box by ID
        """
        self.create_boxes()
        box = StorageService.create_new_storage("Room2", "Shelf2", "Box3")
        result = StorageService.read_storage_by_id(box.storage_id)
        assert result.box == "Box3"

    def test_read_nonexistent_storage_by_id(self):
        """
        Test reading a nonexistent storage box by ID
        """
        with pytest.raises(StorageNotFoundException):
            StorageService.read_storage_by_id("999")

    def test_delete_storage_by_id(self):
        """
        Test deleting a storage box by ID
        """
        self.create_boxes()
        box = StorageService.create_new_storage("Room2", "Shelf2", "Box3")
        StorageService.delete_storage_by_id(box.storage_id)
        with pytest.raises(StorageNotFoundException):
            StorageService.read_storage_by_id(box.storage_id)

    def test_delete_nonexistent_storage_by_id(self):
        """
        Test deleting a nonexistent storage box by ID
        """
        with pytest.raises(StorageNotFoundException):
            StorageService.delete_storage_by_id("999")

    def test_get_box_content(self):
        """
        Test getting the content of a storage box
        """
        self.create_boxes()
        box_content = StorageService.get_box_content("Box1")
        assert len(box_content) == 0

    def test_get_content_of_nonexistent_box(self):
        """
        Test getting the content of a nonexistent storage box
        """
        with pytest.raises(StorageNotFoundException):
            StorageService.get_box_content("NonexistentBox")
