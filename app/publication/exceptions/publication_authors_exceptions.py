"""
This module contains exception classes related to managing publication authors.
"""


class PublicationAuthorsExistsException(Exception):
    """
    Exception raised when trying to create an entry
    that already exists in the database.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class PublicationAuthorsNotFoundException(Exception):
    """
    Exception raised when entry cannot be found
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class EntryAlreadyExistsException(Exception):
    """
    Exception raised when entry already exists
    in the database
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
