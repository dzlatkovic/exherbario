"""This module contains unit tests for a Python project using the `pytest` testing framework."""


import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm.exc import UnmappedInstanceError

from app.tests import TestClass, TestingSessionLocal
from app.users.repository import UserRepository


class TestUserRepo(TestClass):
    """This class tests the user repository"""
    def create_users_for_methods(self):
        """
        It creates four users in the database
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user_repository.create_user("Michael", "Scott", "michael@gmail.com", "password")
            user_repository.create_user("Dwight", "Schrute", "dwight@gmail.com", "password")
            user_repository.create_user("Angela", "Martin", "angela@gmail.com", "password")
            user_repository.create_user("Pam", "Beesly", "pam@gmail.com", "password")

    def test_create_user(self):
        """
        We create a user with the email "michael@gmail.com" and assert
        that the email is "michael@gmail.com" and that the
        user is not a superuser and is active
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com", "password")
            assert user.email == "michael@gmail.com"
            assert user.is_superuser is False
            assert user.is_active is True

    def test_create_user_error(self):
        """
        We create a user, then try to create another user with the same
        email address, which should raise an IntegrityError
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com", "password")
            assert user.is_active is not False
            with pytest.raises(IntegrityError):
                user_repository.create_user("Michael", "Scott", "michael@gmail.com", "password")

    def test_create_super_user(self):
        """
        We create a superuser with the email "michael@gmail.com" and assert
        that the email is "michael@gmail.com" and that
        the user is a superuser
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            superuser = user_repository.create_super_user("Michael", "Scott", "michael@gmail.com",
                                                          "password")
            assert superuser.email == "michael@gmail.com"
            assert superuser.is_superuser is True

    def test_create_super_user_error(self):
        """
        We create a superuser, then try to create another superuser
        with the same email address, which should raise an
        IntegrityError
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            superuser = user_repository.create_super_user("Michael", "Scott", "michael@gmail.com",
                                                          "password")
            assert superuser.is_superuser
            with pytest.raises(IntegrityError):
                user_repository.create_super_user("Michael", "Scott", "michael@gmail.com",
                                                  "password")

    def test_get_user_by_id(self):
        """
        We create a user, then we retrieve that user by its ID and
        assert that the email address is the same
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                               "password")
            retrieved_user = user_repository.get_user_by_id(user.user_id)
            assert retrieved_user.email == "michael@gmail.com"

    def test_get_user_by_id_error(self):
        """
        We create a user, retrieve the user by id, and assert that
        the email is not equal to "dwight@gmail.com"
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                               "password")
            retrieved_user = user_repository.get_user_by_id(user.user_id)
            assert retrieved_user.email != "dwight@gmail.com"

    def test_get_all_users(self):
        """
        It creates a user repository and then gets all the users from the database.
        """
        self.create_users_for_methods()
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            all_users = user_repository.get_all_users()
            assert len(all_users) == 4

    def test_delete_user_by_id(self):
        """
        It deletes a user by id.
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                               "password")
            assert user_repository.delete_user_by_id(user.user_id) is True

    def test_delete_user_by_id_error(self):
        """
        We create a user, then try to delete a user with an invalid id
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                        "password")
            with pytest.raises(UnmappedInstanceError):
                user_repository.delete_user_by_id("invalid id")

    def test_update_user_is_active(self):
        """
        It creates a user, then updates the user's is_active attribute to False.
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user = user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                               "password")
            user = user_repository.update_user_is_active(user.user_id, False)
            assert user.is_active is False

    def test_read_user_by_email(self):
        """
        We create a user with the name "Michael", surname "Scott",
        email "michael@gmail.com" and password "password". Then
        we read the user by email and assert that the name and
        surname are the same as the ones we created the user with
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                        "password")
            user = user_repository.read_user_by_email("michael@gmail.com")
            assert user.name == "Michael"
            assert user.surname == "Scott"

    def test_read_user_by_email_invalid(self):
        """
        If we create a user with a valid email, then we
        should be able to read that user by email
        """
        with TestingSessionLocal() as db:
            user_repository = UserRepository(db)
            user_repository.create_user("Michael", "Scott", "michael@gmail.com",
                                        "password")
            assert user_repository.read_user_by_email("invalid email") is None
