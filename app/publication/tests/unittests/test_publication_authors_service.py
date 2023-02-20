"""
This module contains unit tests for a Python project using the
`pytest` testing framework.
"""


import pytest

from app.publication.exceptions import (EntryAlreadyExistsException,
                                        PublicationAuthorsNotFoundException)
from app.tests import TestClass, TestingSessionLocal
from app.publication.repository import PublicationRepository
from app.users.repository import UserRepository
from app.publication.services import PublicationAuthorsService


class TestPublicationAuthorsService(TestClass):
    """It tests the PublicationAuthorsService class"""
    def test_create_publication(self):
        """
        It creates a new publication and a new author.
        """
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com",
                                                 "password")
            pub = publication_repository.create_publication("1200", "2010",
                                                            "Computer Science",
                                                            "Herbarium API")
            pub_author = PublicationAuthorsService.create_new_publication_authors(author.user_id,
                                                                                  pub.pub_id)
            assert pub_author.publication_id == pub.pub_id
            assert pub_author.user_id == author.user_id

    def test_create_publication_authors_with_invalid_user_id(self):
        """
        `test_create_publication_authors_with_invalid_user_id` tests that
        `PublicationAuthorsService.create_new_publication_authors`
        raises a `ValueError` when given an invalid user id
        """
        with TestingSessionLocal():
            invalid_user_id = "invalid_user_id"
            publication_id = "1234"
            with pytest.raises(ValueError):
                PublicationAuthorsService.create_new_publication_authors(invalid_user_id,
                                                                         publication_id)

    def test_create_publication_authors_with_invalid_publication_id(self):
        """
        It creates a new user, then tries to create a new publication
        authors record with an invalid publication id
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            invalid_publication_id = "invalid_publication_id"
            with pytest.raises(ValueError):
                PublicationAuthorsService.create_new_publication_authors(author.user_id,
                                                                         invalid_publication_id)

    def test_create_duplicate_publication_authors(self):
        """
        This function tests that a publication author cannot be created
        if the author already exists in the publication
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010", "Computer Science",
                                                               "Herbarium API")
            PublicationAuthorsService.create_new_publication_authors(author.user_id, pub.pub_id)
            with pytest.raises(EntryAlreadyExistsException):
                PublicationAuthorsService.create_new_publication_authors(author.user_id,
                                                                         pub.pub_id)

    def test_delete_publication_authors(self):
        """
        This function tests the deletion of a publication author by id
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010",
                                                               "Computer Science", "Herbarium API")
            pub_author = PublicationAuthorsService.create_new_publication_authors(author.user_id,
                                                                                  pub.pub_id)
            answer = PublicationAuthorsService.delete_publication_authors_by_id(
                pub_author.publication_authors_id)
            assert answer is True

    def test_delete_publication_authors_invalid(self):
        """
        This function tests the delete_publication_authors_by_id
        function in the PublicationAuthorsService class
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010", "Computer Science",
                                                               "Herbarium API")
            PublicationAuthorsService.create_new_publication_authors(author.user_id, pub.pub_id)
            with pytest.raises(PublicationAuthorsNotFoundException):
                PublicationAuthorsService.delete_publication_authors_by_id("invalid_id")
