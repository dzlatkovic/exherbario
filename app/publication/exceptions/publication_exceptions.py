"""
This module contains exception classes related to managing publications.
"""


class PublicationExceptionDoi(Exception):
    """
    Exception raised when trying to create a publication
    that already exists in the database.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class PublicationNotFoundException(Exception):
    """
    Exception raised when publication cannot be found
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
