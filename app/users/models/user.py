"""
This module contains the User model, which represents
a user in the database.
"""


from sqlalchemy import Column, DateTime, String, Boolean, UniqueConstraint
from app.db import Base, new_id


class User(Base):
    """The User model represents a user in the database."""
    __tablename__ = "users"
    __table_args__ = (UniqueConstraint("orcid", name="uq_users_orcid"),)
    user_id = Column(String(50), primary_key=True, default=new_id, autoincrement=False)
    name = Column(String(50))
    surname = Column(String(50))
    email = Column(String(100), unique=True)
    password = Column(String(200))
    is_active = Column(Boolean)
    is_superuser = Column(Boolean, default=False)
    # Set only after ORCID authenticates the person and they confirm the link; never typed in.
    orcid = Column(String(19))
    orcid_name = Column(String(200))
    orcid_linked_at = Column(DateTime)

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
