
class NoPointsPassedError(Exception):
    def __init__(self, message="No points passed the filters."):
        super().__init__(message)
