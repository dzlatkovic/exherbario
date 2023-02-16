"""
Module to handle exceptions related to users.
"""


class UserInvalidPassword(Exception):
    """
    This class is used to raise an exception when a user
    enters an invalid password
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class UserNotSuperUser(Exception):
    """
    Exception raised when a user who is not a superuser
    attempts to access a resource.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
