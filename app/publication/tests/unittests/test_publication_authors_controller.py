"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


import pytest
from fastapi import HTTPException

from app.tests import TestClass, TestingSessionLocal
from app.publication.repository import PublicationRepository
from app.users.repository import UserRepository
from app.publication.controller import PublicationAuthorsController


class TestPublicationAuthorsController(TestClass):
    """It tests the PublicationAuthorsController class"""
    def test_create_publication(self):
        """
        This function creates a new publication and a new author,
        then creates a new publication_author record with the
        author's user_id and the publication's pub_id
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = publication_repository.create_publication("1200", "2010",
                                                            "Computer Science", "Herbarium API")
            pub_author = PublicationAuthorsController.create_new_publication_authors(author.user_id,
                                                                                     pub.pub_id)
            assert pub_author.publication_id == pub.pub_id
            assert pub_author.user_id == author.user_id

    def test_create_publication_authors_with_invalid_user_id(self):
        """
        It tests the create_new_publication_authors function
        in the PublicationAuthorsController class.
        """
        with TestingSessionLocal():
            invalid_user_id = "invalid_user_id"
            publication_id = "1234"
            with pytest.raises(HTTPException) as error:
                PublicationAuthorsController.create_new_publication_authors(invalid_user_id,
                                                                            publication_id)
            assert error.value.status_code == 400
            assert "invalid_user" in error.value.detail

    def test_create_publication_authors_with_invalid_publication_id(self):
        """
        If a user tries to create a publication author with an invalid
        publication id, then an HTTPException is raised.

        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            invalid_publication_id = "invalid_publication_id"
            with pytest.raises(HTTPException) as error:
                PublicationAuthorsController.create_new_publication_authors(author.user_id,
                                                                            invalid_publication_id)
            assert error.value.status_code == 400
            assert "invalid_publication_id" in error.value.detail

    def test_create_duplicate_publication_authors(self):
        """
        This function tests that a user cannot create a
        duplicate publication author entry
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com",
                                                 "password")
            pub = PublicationRepository(db).create_publication("1200", "2010",
                                                               "Computer Science",
                                                               "Herbarium API")
            PublicationAuthorsController.create_new_publication_authors(author.user_id,
                                                                        pub.pub_id)
            with pytest.raises(HTTPException) as error:
                PublicationAuthorsController.create_new_publication_authors(author.user_id,
                                                                            pub.pub_id)
            assert error.value.status_code == 400
            assert "Entry already exists" in error.value.detail

    def test_delete_publication_authors_by_id(self):
        """
        This function tests the delete_publication_authors_by_id
        function in the PublicationAuthorsController class
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith",
                                                 "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010",
                                                               "Computer Science",
                                                               "Herbarium API")
            pub_author = PublicationAuthorsController.create_new_publication_authors(
                author.user_id, pub.pub_id)
            PublicationAuthorsController.delete_publication_authors_by_id(
                pub_author.publication_authors_id)
            with pytest.raises(HTTPException) as error:
                PublicationAuthorsController.delete_publication_authors_by_id(
                    pub_author.publication_authors_id)
            assert error.value.status_code == 400

    def test_delete_publication_authors_invalid(self):
        """
        This function tests the delete_publication_authors_by_id
        function in the PublicationAuthorsController class
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user(
                "John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication(
                "1200", "2010", "Computer Science", "Herbarium API")
            PublicationAuthorsController.create_new_publication_authors(author.user_id, pub.pub_id)
            with pytest.raises(HTTPException) as error:
                PublicationAuthorsController.delete_publication_authors_by_id("invalid_id")
            assert error.value.status_code == 400
