class PublicationAuthorsExistsException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class PublicationAuthorsNotFoundException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
