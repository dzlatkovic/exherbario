class FieldLocExceptionCode(Exception):

    def __init__(self, message, code):
        self.message = message
        self.code = code


class FieldLocNotFoundException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
