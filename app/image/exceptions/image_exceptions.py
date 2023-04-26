class InvalidImageFileException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class InvalidImageFormatException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class MaximumDimensionsExceededException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class ImageNotFoundException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class MissingFileException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
