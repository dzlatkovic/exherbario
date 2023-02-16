"""
Custom exceptions for field location operations.

This module defines custom exception classes for handling errors related to field location
operations. The exceptions provide specific error messages and codes, and can be raised in the
service layer of the field location module.
"""


class FieldLocExceptionCode(Exception):
    """
    Exception class for handling field location exceptions with custom error codes.

    This exception class provides a specific error message and code for field location exceptions.
    It can be raised in the service layer of the field location module.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class FieldLocNotFoundException(Exception):
    """
    Exception class for handling field location not found exceptions.

    This exception class provides a specific error message and code for
    field location not found exceptions.
    It can be raised in the service layer of the field location module.
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
