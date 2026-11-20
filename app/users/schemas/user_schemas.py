"""
This module defines Pydantic schemas for working with user data.
Includes schemas for representing a user, creating a new user, and
logging in a user.
"""


from pydantic import BaseModel, ConfigDict
from pydantic import UUID4, EmailStr


class UserSchema(BaseModel):
    """Pydantic schema representing a user."""
    user_id: UUID4
    name: str
    surname: str
    email: str
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)


class UserSchemaIn(BaseModel):
    """Pydantic schema for creating a new user."""
    name: str
    surname: str
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)


class UserSchemaLogin(BaseModel):
    """Pydantic schema for logging in a user."""
    email: EmailStr
    password: str

    model_config = ConfigDict(from_attributes=True)
