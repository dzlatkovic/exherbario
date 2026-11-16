"""
This module contains the User model, which represents
a user in the database.
"""


from sqlalchemy import Column, String, Boolean
from app.db import Base, new_id


class User(Base):
    """The User model represents a user in the database."""
    __tablename__ = "users"
    user_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    name = Column(String(50))
    surname = Column(String(50))
    email = Column(String(100), unique=True)
    password = Column(String(200))
    is_active = Column(Boolean)
    is_superuser = Column(Boolean, default=False)

    def __init__(self, name: str, surname: str, email: str, password: str,
                 is_active: bool = True, is_superuser: bool = False):
        """Initialize a new User instance
        :param name: The name of the user
        :param surname: The surname of the user
        :param email: The email address of the user
        :param password: The password of the user
        :param is_active: Indicates if the user is active. Defaults to True
        :param is_superuser: Indicates if the user is a superuser. Defaults to False
        """
        self.name = name
        self.surname = surname
        self.email = email
        self.password = password
        self.is_active = is_active
        self.is_superuser = is_superuser
