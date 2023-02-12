class PublicationExceptionDoi(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class PublicationNotFoundException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
