class PlantNetRequestFailedException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code


class MissingPlantNetIdentificationException(Exception):
    def __init__(self, message, code):
        self.message = message
        self.code = code
