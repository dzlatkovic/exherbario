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
