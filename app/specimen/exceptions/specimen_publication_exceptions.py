class SpecimenPublicationExistsException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class SpecimenPublicationNotFoundException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
