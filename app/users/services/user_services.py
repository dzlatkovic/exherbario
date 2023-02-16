"""This module provides services for managing user-related functionality."""


import hashlib
from app.users.repository.user_repository import UserRepository
from app.db.database import SessionLocal
from app.users.exceptions import UserInvalidPassword


class UserServices:
    """
    This class provides services for managing user-related functionality.
    """
    @staticmethod
    def create_user(name: str, surname: str, email, password: str):
        """
        Create a new user with the given name, surname, email, and password
        :param name: The first name of the user
        :type name: str
        :param surname: The last name of the user
        :type surname: str
        :param email: The email address of the user
        :type email: str
        :param password: The password of the user
        :type password: str
        :return: The newly created user
        :rtype: User
        """
        with SessionLocal() as db:
            try:
                user_repository = UserRepository(db)
                hashed_password = hashlib.sha256(bytes(password, "utf-8")).hexdigest()
                return user_repository.create_user(name, surname, email, hashed_password)
            except Exception as error:
                raise error

    @staticmethod
    def create_super_user(name, surname, email, password):
        """
        Create a new superuser with the given name, surname, email, and password
        :param name: The first name of the superuser
        :type name: str
        :param surname: The last name of the superuser
        :type surname: str
        :param email: The email address of the superuser
        :type email: str
        :param password: The password of the superuser
        :type password: str
        :return: The newly created superuser
        :rtype: SuperUser
        """
        with SessionLocal() as db:
            try:
                user_repository = UserRepository(db)
                hashed_password = hashlib.sha256(bytes(password, "utf-8")).hexdigest()
                return user_repository.create_super_user(name, surname, email, hashed_password)
            except Exception as error:
                raise error

    @staticmethod
    def get_user_by_id(user_id: str):
        """
        Get the user with the given ID
        :param user_id: The ID of the user
        :type user_id: str
        :return: The user with the given ID, or None if the user does not exist
        :rtype: User or None
        """
        with SessionLocal() as db:
            user_repository = UserRepository(db)
            return user_repository.get_user_by_id(user_id)

    @staticmethod
    def get_all_users():
        """
        Get a list of all users
        :return: A list of all users
        :rtype: List[User]
        """
        with SessionLocal() as db:
            user_repository = UserRepository(db)
            return user_repository.get_all_users()

    @staticmethod
    def delete_user_by_id(user_id: str):
        """
        Delete the user with the given ID
        :param user_id: The ID of the user
        :type user_id: str
        :return: True if the user was deleted, False if the user does not exist
        :rtype: bool
        """
        try:
            with SessionLocal() as db:
                user_repository = UserRepository(db)
                return user_repository.delete_user_by_id(user_id)
        except Exception as error:
            raise error

    @staticmethod
    def update_user_is_active(user_id: str, is_active: bool):
        """
        Update the is_active attribute of the user with the given ID
        :param user_id: The ID of the user
        :type user_id: str
        :param is_active: The new value of the is_active attribute
        :type is_active: bool
        :return: True if the user was updated, False if the user does not exist
        :rtype: bool
        """
        with SessionLocal() as db:
            try:
                user_repository = UserRepository(db)
                return user_repository.update_user_is_active(user_id, is_active)
            except Exception as error:
                raise error

    @staticmethod
    def login_user(email: str, password: str):
        """Authenticate a user with the given email and password
        :param email: The email address of the user
        :type email: str
        :param password: The password of the user
        :type password: str
        :return: The authenticated user
        :rtype: User
        """
        with SessionLocal() as db:
            try:
                user_repository = UserRepository(db)
                user = user_repository.read_user_by_email(email)
                if hashlib.sha256(bytes(password, "utf-8")).hexdigest() != user.password:
                    raise UserInvalidPassword(message="Invalid password for user", code=401)
                return user
            except Exception as error:
                raise error
