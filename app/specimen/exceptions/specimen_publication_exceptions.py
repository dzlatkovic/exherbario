"""This module provides custom exception classes for specimen publications."""


class SpecimenPublicationExistsException(Exception):
    """
    Exception raised when a specimen publication already exists
    :param message: The error message
    :type message: str
    :param code: The HTTP status code to use in the response
    :type code: int
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class SpecimenPublicationNotFoundException(Exception):
    """
    Exception raised when a specimen publication is not found
    :param message: The error message
    :type message: str
    :param code: The HTTP status code to use in the response
    :type code: int
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
