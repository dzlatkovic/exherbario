import pytest

from app.publication.exceptions import EntryAlreadyExistsException, PublicationAuthorsNotFoundException
from app.tests import TestClass, TestingSessionLocal
from app.publication.repository import PublicationAuthorsRepository, PublicationRepository
from app.users.repository import UserRepository


class TestPublicationAuthorsRepo(TestClass):

    def test_create_publication(self):
        with TestingSessionLocal() as db:
            publication_repository = PublicationRepository(db)
            publication_authors_repository = PublicationAuthorsRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = publication_repository.create_publication("1200", "2010",
                                                            "Computer Science", "Herbarium API")
            pub_author = publication_authors_repository.create_publication_authors(author.user_id, pub.pub_id)
            assert pub_author.publication_id == pub.pub_id
            assert pub_author.user_id == author.user_id

    def test_create_publication_authors_with_invalid_user_id(self):
        with TestingSessionLocal() as db:
            publication_authors_repository = PublicationAuthorsRepository(db)
            invalid_user_id = "invalid_user_id"
            publication_id = "1234"
            with pytest.raises(ValueError):
                publication_authors_repository.create_publication_authors(invalid_user_id, publication_id)

    def test_create_publication_authors_with_invalid_publication_id(self):
        with TestingSessionLocal() as db:
            publication_authors_repository = PublicationAuthorsRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            invalid_publication_id = "invalid_publication_id"
            with pytest.raises(ValueError):
                publication_authors_repository.create_publication_authors(author.user_id, invalid_publication_id)

    def test_create_duplicate_publication_authors(self):
        with TestingSessionLocal() as db:
            publication_authors_repository = PublicationAuthorsRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010", "Computer Science", "Herbarium API")
            publication_authors_repository.create_publication_authors(author.user_id, pub.pub_id)
            with pytest.raises(EntryAlreadyExistsException):
                publication_authors_repository.create_publication_authors(author.user_id, pub.pub_id)

    def test_delete_publication_authors(self):
        with TestingSessionLocal() as db:
            publication_authors_repository = PublicationAuthorsRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010", "Computer Science", "Herbarium API")
            pub_author = publication_authors_repository.create_publication_authors(author.user_id, pub.pub_id)
            answer = publication_authors_repository.delete_publication_authors_by_id(
                pub_author.publication_authors_id)
            assert answer is True

    def test_delete_publication_authors_invalid(self):
        with TestingSessionLocal() as db:
            publication_authors_repository = PublicationAuthorsRepository(db)
            user_repository = UserRepository(db)
            author = user_repository.create_user("John", "Smith", "john@example.com", "password")
            pub = PublicationRepository(db).create_publication("1200", "2010", "Computer Science", "Herbarium API")
            publication_authors_repository.create_publication_authors(author.user_id, pub.pub_id)
            with pytest.raises(PublicationAuthorsNotFoundException):
                publication_authors_repository.delete_publication_authors_by_id("invalid_id")
