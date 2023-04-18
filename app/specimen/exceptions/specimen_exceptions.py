"""This module provides custom exception classes for specimen """


class SpecimenExceptionRegNo(Exception):
    """
    This class is used to raise an exception when the specimen
    registration number is not found in the database.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class SpecimenNotFoundException(Exception):
    """
    This class is used to raise an exception when a specimen is not found
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class InvalidDateRangeException(Exception):
    """
    This class is used to raise an exception when a specimen is not found
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class SearchResultsNotFoundException(Exception):
    """
    Exception raised when no search results are found.

    :param message: A description of the exception.
    :type message: str
    :param code: An error code associated with the exception.
    :type code: int
    """

    def __init__(self, message, code):
        self.message = message
        self.code = code
