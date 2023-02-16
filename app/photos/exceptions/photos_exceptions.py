"""
Module to handle exceptions related to photos.
"""


class PhotosNotFoundException(Exception):
    """
    Exception raised when photos cannot be found
    :param message: the error message
    :param code: the error code
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class IdenticalPhotosException(Exception):
    """
    Exception raised when two identical paths are
    provided for field_photo and specimen_photo
    :param message: the error message
    :param code: the error code
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code


class PhotoAlreadyExistsException(Exception):
    """
    Exception raised when photo already exists in
    the database
    :param message: the error message
    :param code: the error code
    """
    def __init__(self, message, code):
        self.message = message
        self.code = code
