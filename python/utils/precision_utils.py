
from enum import IntEnum
from typing import Dict
from functools import lru_cache

from utils.config_loader import ConfigLoader

# get logger
import logging
logger = logging.getLogger(__name__)

class Precision(IntEnum):
    INSENSITIVE = 0
    COARSE      = 1
    LOW         = 2
    MEDIUM      = 3
    HIGH        = 4
    SATURATED   = 5

    @classmethod
    def from_string(cls, s: str) -> "Precision":
        try:
            return cls[s.strip().upper()]
        except KeyError:
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
        config_loader = ConfigLoader("OptimizerConfig.yml")

        try:
            thresholds: Dict[str, float] = config_loader.get('precision_thresholds')
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
        """
        key = str(self)  # e.g., "low"
        thresholds = self._load_thresholds()

        if key not in thresholds:
            raise KeyError(f"Missing threshold for level '{key}'")

        return thresholds[key]
