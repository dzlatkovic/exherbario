"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


import pytest

from app.photos.exceptions import (IdenticalPhotosException,
                                   PhotoAlreadyExistsException,
                                   PhotosNotFoundException)
from app.tests import TestClass
from app.photos.services import PhotosService


class TestPhotosService(TestClass):
    """This class tests the PhotosService class"""
    def create_photos(self):
        """
        It creates two new photos records
        """
        PhotosService.create_new_photos("/path/to/field/photo.jpg",
                                        "/path/to/specimen/photo.jpg")
        PhotosService.create_new_photos("/path/to/field/photo_2.jpg",
                                        "/path/to/specimen/photo_2.jpg")

    def test_create_new_photos(self):
        """
        Test creating a new photos record
        """
        photos = PhotosService.create_new_photos("/path/to/field/photo_3.jpg",
                                                 "/path/to/specimen/photo_3.jpg")
        assert photos.field_photo == "/path/to/field/photo_3.jpg"
        assert photos.specimen_photo == "/path/to/specimen/photo_3.jpg"

    def test_create_identical_photos(self):
        """
        Test creating a photos record with identical photos
        """
        with pytest.raises(IdenticalPhotosException):
            PhotosService.create_new_photos("/path/to/photo.jpg",
                                            "/path/to/photo.jpg")

    def test_create_duplicate_photos(self):
        """
        Test creating a photos record that already exists
        """
        self.create_photos()
        with pytest.raises(PhotoAlreadyExistsException):
            PhotosService.create_new_photos("/path/to/field/photo.jpg",
                                            "/path/to/specimen/photo.jpg")

    def test_read_all_photos(self):
        """
        Test reading all photos records
        """
        self.create_photos()
        photos = PhotosService.read_all_photos()
        assert len(photos) == 2

    def test_read_photos_by_id(self):
        """
        Test reading a photos record by ID
        """
        photos = PhotosService.create_new_photos("/path/to/field/photo_4.jpg",
                                                 "/path/to/specimen/photo_4.jpg")
        read_photo = PhotosService.read_photos_by_id(photos.photos_id)
        assert photos.field_photo == read_photo.field_photo
        assert photos.specimen_photo == read_photo.specimen_photo

    def test_read_nonexistent_photos(self):
        """
        Test reading a nonexistent photos record by ID
        """
        with pytest.raises(PhotosNotFoundException):
            PhotosService.read_photos_by_id("nonexistent_id")

    def test_delete_photos_by_id(self):
        """
        Test deleting a photos record by ID
        """
        photos = PhotosService.create_new_photos("/path/to/field/photo_5.jpg",
                                                 "/path/to/specimen/photo_5.jpg")
        PhotosService.delete_photos_by_id(photos.photos_id)
        with pytest.raises(PhotosNotFoundException):
            PhotosService.read_photos_by_id(photos.photos_id)

    def test_delete_nonexistent_photos(self):
        """
        Test deleting a nonexistent photos record by ID
        """
        with pytest.raises(PhotosNotFoundException):
            PhotosService.delete_photos_by_id("nonexistent_id")
