"""
This module provides custom exception classes for storage boxes.
"""


class StorageExceptionBox(Exception):
    """
    Exception raised when a storage box
    already exists in the database.
    """
    def __init__(self, message, code):
        """
        Initialize the StorageExceptionBox object
        :param message: The error message
        :type message: str
        :param code: The HTTP error code to return
        :type code: int
        :returns: None
        """
        self.message = message
        self.code = code


class StorageNotFoundException(Exception):
    """Exception raised when a storage box is not found."""
    def __init__(self, message, code):
        """
        Initialize the StorageNotFoundException object
        :param message: The error message
        :type message: str
        :param code: The HTTP error code to return
        :type code: int
        :returns: None
        """
        self.message = message
        self.code = code
