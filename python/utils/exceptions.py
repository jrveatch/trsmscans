
from typing import Optional
from logging import Logger

class NoPointsPassedError(Exception):
    def __init__(self,
                 message="No points passed the filters.",
                 logger: Optional[Logger] = None):
        if logger:
            logger.error(message)
        super().__init__(message)
