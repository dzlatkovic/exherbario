class TaxonDoesNotExistException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class TaxonAlreadyExistException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class TaxonomyServiceException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message


class GBIFServiceException(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message
