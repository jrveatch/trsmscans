
from enum import IntEnum
from typing import Dict
from functools import lru_cache

from utils.config_loader import ConfigLoader

# get logger
import logging
logger = logging.getLogger(__name__)

class Precision(IntEnum):
    MISSING     = -1
    INSENSITIVE = 0
    SATURATED   = 1
    COARSE      = 2
    LOW         = 3
    MEDIUM      = 4
    HIGH        = 5

    @classmethod
    def from_string(cls, s: str) -> "Precision":
        s_clean = s.strip().upper()
        if s_clean in cls.__members__:
            return cls[s_clean]
        if s_clean in {"", "NAN", "NONE"}:
            return cls.MISSING
        raise ValueError(f"Invalid precision level: {s}")

    def __str__(self) -> str:
        return self.name.lower()

    @staticmethod
    @lru_cache()
    def _load_thresholds() -> Dict[str, float]:
        """
        Load precision threshold values from the configuration file.

        Returns:
            Dict[str, float]: A dictionary mapping precision levels
                            (e.g., 'coarse', 'low', 'medium', 'high')
                            to their corresponding threshold values.

        Raises:
            Exception: If the configuration section is missing or invalid.
        """
        optimizer_config = ConfigLoader("OptimizerConfig.yml")

        try:
            thresholds: Dict[str, float] = optimizer_config.get('precision_thresholds')
        except Exception as e:
            logger.exception(e)
            raise

        return thresholds

    @classmethod
    def all_thresholds(cls) -> Dict[str, float]:
        return cls._load_thresholds()

    def threshold(self) -> float:
        """
        Get the threshold value for a given precision level name.

        Returns:
            float: The configured threshold for the specified level.

        Raises:
            KeyError: If the level is not found in the configuration.
            ValueError if the precision is MISSING.
        """
        if self == Precision.MISSING:
            raise ValueError("Cannot get threshold for MISSING precision level.")

        key = str(self)  # e.g., "low"
        thresholds = self._load_thresholds()

        if key not in thresholds:
            raise KeyError(f"Missing threshold for level '{key}'")

        return thresholds[key]
