"""This module defines the routes for user operations."""


from fastapi import APIRouter, Depends
from app.users.controller import UserController
from app.users.schemas import UserSchema, UserSchemaIn, UserSchemaLogin
from app.users.controller.user_auth_controller import JWTBearer


user_router = APIRouter(tags=["Users"], prefix="/api/users")


@user_router.post("/add-new-user", response_model=UserSchema,
                  dependencies=[Depends(JWTBearer("super_user"))])
def create_user(user: UserSchemaIn):
    """
    Creates a new user
    :param user: UserSchemaIn object
    :return: UserSchema object
    """
    return UserController.create_user(user.name, user.surname, user.email, user.password)


@user_router.post("/add-new-super-user", response_model=UserSchema)
def create_super_user(user: UserSchemaIn):
    """
    Creates a new superuser
    :param user: UserSchemaIn object
    :return: UserSchema object
    """
    return UserController.create_super_user(user.name, user.surname, user.email, user.password)


@user_router.post("/login")
def login_user(user: UserSchemaLogin):
    """
    Logs in a user
    :param user: UserSchemaLogin object
    :return: JWT token
    """
    return UserController.login_user(user.email, user.password)


@user_router.get("/id", response_model=UserSchema)
def get_user_by_id(user_id: str):
    """
    Gets a user by ID
    :param user_id: ID of the user
    :return: UserSchema object
    """
    return UserController.get_user_by_id(user_id)


@user_router.get("/get-all-users", response_model=list[UserSchema])
def get_all_users():
    """
    Gets all users
    :return: List of UserSchema objects
    """
    return UserController.get_all_users()


@user_router.delete("/delete-user", dependencies=[Depends(JWTBearer("super_user"))])
def delete_user_by_id(user_id: str):
    """
    Deletes a user by ID
    :param user_id: ID of the user
    :return: Success message
    """
    return UserController.delete_user_by_id(user_id)


@user_router.put("/update/is_active", response_model=UserSchema)
def update_user(user_id: str, is_active: bool):
    """
    Updates a user's is_active status
    :param user_id: ID of the user
    :param is_active: New value of is_active
    :return: UserSchema object
    """
    return UserController.update_user_is_active(user_id, is_active)
