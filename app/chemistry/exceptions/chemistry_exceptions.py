class ChemistryError(Exception):
    """A chemistry workflow error with an API status code."""

    def __init__(self, code: int, message: str):
        super().__init__(message)
        self.code = code
