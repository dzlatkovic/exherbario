"""This module contains unit tests for a Python project using the `pytest` testing framework."""

import pytest
from fastapi import HTTPException

from app.tests import TestClass
from app.users.controller import UserController


class TestUserController(TestClass):
    """This class tests the user repository"""

    def create_users_for_methods(self):
        """
        It creates four users in the database
        """
        UserController.create_user("Michael", "Scott", "michael@gmail.com", "password")
        UserController.create_user("Dwight", "Schrute", "dwight@gmail.com", "password")
        UserController.create_user("Angela", "Martin", "angela@gmail.com", "password")
        UserController.create_user("Pam", "Beesly", "pam@gmail.com", "password")

    def test_create_user(self):
        """
        We create a user with the email "michael@gmail.com" and assert
        that the email is "michael@gmail.com" and that the
        user is not a superuser and is active
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com", "password")
        assert user.email == "michael@gmail.com"
        assert user.is_superuser is False
        assert user.is_active is True

    def test_create_user_error(self):
        """
        We create a user, then try to create another user with the same
        email address, which should raise an IntegrityError
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com", "password")
        assert user.is_active is not False
        with pytest.raises(HTTPException) as error:
            UserController.create_user("Michael", "Scott", "michael@gmail.com", "password")
        assert error.value.status_code == 400

    def test_create_super_user(self):
        """
        We create a superuser with the email "michael@gmail.com" and assert
        that the email is "michael@gmail.com" and that
        the user is a superuser
        """
        superuser = UserController.create_super_user("Michael", "Scott", "michael@gmail.com",
                                                     "password")
        assert superuser.email == "michael@gmail.com"
        assert superuser.is_superuser is True

    def test_create_super_user_error(self):
        """
        We create a superuser, then try to create another superuser
        with the same email address, which should raise an
        IntegrityError
        """
        superuser = UserController.create_super_user("Michael", "Scott", "michael@gmail.com",
                                                     "password")
        assert superuser.is_superuser
        with pytest.raises(HTTPException) as error:
            UserController.create_super_user("Michael", "Scott", "michael@gmail.com",
                                             "password")
        assert error.value.status_code == 400

    def test_get_user_by_id(self):
        """
        We create a user, then we retrieve that user by its ID and
        assert that the email address is the same
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com",
                                          "password")
        retrieved_user = UserController.get_user_by_id(user.user_id)
        assert retrieved_user.email == "michael@gmail.com"

    def test_get_user_by_id_error(self):
        """
        We create a user, retrieve the user by id, and assert that
        the email is not equal to "dwight@gmail.com"
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com",
                                          "password")
        retrieved_user = UserController.get_user_by_id(user.user_id)
        assert retrieved_user.email != "dwight@gmail.com"

    def test_get_all_users(self):
        """
        It creates a user repository and then gets all the users from the database.
        """
        self.create_users_for_methods()
        all_users = UserController.get_all_users()
        assert len(all_users) == 4

    def test_delete_user_by_id(self):
        """
        It deletes a user by id.
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com",
                                          "password")
        response = UserController.delete_user_by_id(user.user_id)
        assert response.status_code == 200

    def test_delete_user_by_id_error(self):
        """
        We create a user, then try to delete a user with an invalid id
        """
        UserController.create_user("Michael", "Scott", "michael@gmail.com",
                                   "password")
        with pytest.raises(HTTPException):
            UserController.delete_user_by_id("invalid id")

    def test_update_user_is_active(self):
        """
        It creates a user, then updates the user's is_active attribute to False.
        """
        user = UserController.create_user("Michael", "Scott", "michael@gmail.com",
                                          "password")
        user = UserController.update_user_is_active(user.user_id, False)
        assert user.is_active is False
