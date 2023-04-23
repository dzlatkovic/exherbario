class SpecimenDoesNotExistException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class DataAlreadyExistException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class UnsuccessfulAPIRequestException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class MissingGPSException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
