"""
This module contains the `UserRepository` class, which is responsible
for database interactions with the `User` model. It provides methods for
creating, reading, updating, and deleting users, as well as retrieving all
users from the database
"""


from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from app.users.models import User


class UserRepository:
    """
    This class contains methods to interact with the User model in the database.
    """
    def __init__(self, db: Session):
        """
        Constructor method
        :param db: Database session object
        """
        self.db = db

    def create_user(self, name: str, surname: str, email, password: str):
        """
        Creates a new user in the database
        :param name: The name of the user
        :param surname: The surname of the user
        :param email: The email of the user
        :param password: The password of the user
        """
        try:
            user = User(name, surname, email, password)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as error:
            raise error

    def create_super_user(self, name: str, surname: str, email, password: str):
        """
        Creates a new superuser in the database
        :param name: The name of the user
        :param surname: The surname of the use
        :param email: The email of the user
        :param password: The password of the user
        """
        try:
            user = User(name=name, surname=surname, email=email, password=password,
                        is_superuser=True)
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except IntegrityError as error:
            raise error

    def get_user_by_id(self, user_id: str):
        """
        Gets a user by their id
        :param user_id: The id of the user
        """
        return self.db.query(User).filter(User.user_id == user_id).first()

    def get_all_users(self):
        """
        Gets all users in the database.
        """
        return self.db.query(User).all()

    def delete_user_by_id(self, user_id: str):
        """
        Deletes a user by their id
        :param user_id: The id of the user
        """
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()
            self.db.delete(user)
            self.db.commit()
            return True
        except Exception as error:
            raise error

    def update_user_is_active(self, user_id: str, is_active: bool):
        """
        Updates the is_active status of a user by their id
        :param user_id: The id of the user
        :param is_active: The new is_active status of the user
        """
        try:
            user = self.db.query(User).filter(User.user_id == user_id).first()
            user.is_active = is_active
            self.db.add(user)
            self.db.commit()
            self.db.refresh(user)
            return user
        except Exception as error:
            raise error

    def read_user_by_email(self, email: str):
        """
        Gets a user by their email
        :param email: The email of the user
        """
        user = self.db.query(User).filter(User.email == email).first()
        return user
