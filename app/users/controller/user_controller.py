"""Module for user controller."""


from fastapi import HTTPException, Response
from sqlalchemy.exc import IntegrityError
from app.users.services import UserServices, signJWT
from app.users.exceptions import UserInvalidPassword


class UserController:
    """This class is responsible for handling user related requests"""
    @staticmethod
    def create_user(name, surname, email, password):
        """Create a new classic user
        :param name: The name of the new user
        :param surname: The surname of the new user
        :param email: The email of the new user
        :param password: The password of the new user
        """
        try:
            user = UserServices.create_user(name, surname, email, password)
            return user
        except IntegrityError as error:
            raise HTTPException(status_code=400,
                                detail=f"User with provided email: "
                                       f"{email} already exists.") from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def create_super_user(name, surname, email, password):
        """Create a new superuser
        :param name: The name of the new superuser
        :param surname: The surname of the new superuser
        :param email: The email of the new superuser
        :param password: The password of the new superuser
        """
        try:
            user = UserServices.create_super_user(name, surname, email, password)
            return user
        except IntegrityError:
            raise HTTPException(status_code=400,
                                detail=f"User with provided email: {email} already exists.")
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def login_user(email, password):
        """Log in user
        :param email: The email of the user
        :param password: The password of the user
        """
        try:
            user = UserServices.login_user(email, password)
            if user.is_superuser:
                return signJWT(user.user_id, "super_user")
            return signJWT(user.user_id, "classic_user")
        except UserInvalidPassword as error:
            raise HTTPException(status_code=error.code, detail=error.message) from error
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error

    @staticmethod
    def get_user_by_id(user_id: str):
        """Get a user by ID
        :param user_id: The ID of the user
        """
        user = UserServices.get_user_by_id(user_id)
        if user:
            return user
        raise HTTPException(status_code=400,
                            detail=f"user with provided id {user_id} does not exist")

    @staticmethod
    def get_all_users():
        """Get all users."""
        return UserServices.get_all_users()

    @staticmethod
    def delete_user_by_id(user_id: str):
        """Delete a user by ID
        :param user_id: The ID of the user to delete
        """
        try:
            UserServices.delete_user_by_id(user_id)
            return Response(content=f"User with the id: {user_id} is deleted from the database.")
        except Exception as error:
            raise HTTPException(status_code=400, detail=str(error)) from error

    @staticmethod
    def update_user_is_active(user_id: str, is_active: bool):
        """Update the is_active flag of a user
        :param user_id: The ID of the user
        :param is_active: The new value of the is_active
        """
        try:
            return UserServices.update_user_is_active(user_id, is_active)
        except Exception as error:
            raise HTTPException(status_code=500, detail=str(error)) from error
