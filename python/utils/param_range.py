
# standard libraries
import logging
from typing import Any, Dict, Optional

# local modules
from utils.math_utils import round_sig

# class to hold and update ranges for a single model parameter
class ParamRange:

    def __init__(self,
                 name: str,
                 param_info: Dict[str, Any]):

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize parameter name
        self.name = name

        # initialize parameter full name
        self.full_name = param_info['fullname']

        # initialize bounds
        self.min_value = param_info['min']
        self.max_value = param_info['max']

    @property
    def name(self) -> str:
        """Name of the parameter"""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Set the name property"""
        self.__name = new_name

    @property
    def full_name(self) -> str:
        """Full name of the parameter"""
        return self.__full_name

    @full_name.setter
    def full_name(self,
                  new_full_name: str) -> None:
        """Set the full name property"""
        self.__full_name = new_full_name

    @property
    def low(self) -> float:
        """Low value of the parameter range"""
        return self.__low

    @low.setter
    def low(self,
            new_low: float) -> None:
        """Set the low value, clamped to the min bound."""
        self.__low = new_low
        if new_low < self.min_value:
            self.__low = self.min_value

    @property
    def high(self) -> float:
        """High value of the parameter range"""
        return self.__high

    @high.setter
    def high(self,
             new_high: float) -> None:
        """Set the high value, clamped to the max bound."""
        self.__high = new_high
        if new_high > self.max_value:
            self.__high = self.max_value

    @property
    def min_value(self) -> float:
        """Minimum bound of the parameter range"""
        return self.__min_value

    @min_value.setter
    def min_value(self,
                    new_min_value: float) -> None:
        self.__min_value = new_min_value
        """If __low hasn't been set yet, initialize it to min_value.
        Otherwise, ensure __low stays within bounds."""
        if hasattr(self, '_ParamRange__low'):
            if self.low < self.min_value:
                self.low = self.min_value
        else:
            self.__low = self.__min_value

    @property
    def max_value(self) -> float:
        """Maximum bound of the parameter range"""
        return self.__max_value

    @max_value.setter
    def max_value(self,
                    new_max_value: float) -> None:
        self.__max_value = new_max_value
        """If __high hasn't been set yet, initialize it to max_value.
        Otherwise, ensure __high stays within bounds."""
        if hasattr(self, '_ParamRange__high'):
            if self.high > self.max_value:
                self.high = self.max_value
        else:
            self.__high = self.__max_value

    @property
    def center(self) -> float:
        """Center value of the parameter range"""
        return (self.low + self.high) / 2

    @property
    def range(self) -> tuple:
        """High and low values of the parameter range"""
        return (self.low, self.high)

    @property
    def width(self) -> float:
        """Width of the parameter range"""
        return abs(self.high - self.low)

    def scale_width(self,
                    new_val: Optional[float] = None,
                    range_scale: float = 1.0) -> None:
        """Set new central value, range, low and high based on scaling"""
        # complain and exit if there is nothing to do
        if new_val is None and range_scale == 1.0:
            self.logger.warning("Attempting to update parameter with no new information... returning...")
            return

        width = self.width
        center = self.center

        # scale width by given value
        width *= range_scale

        # set new low and high using the half width
        self.set_low_high(new_low=center - width / 2,
                          new_high=center + width / 2)

        # adjust low and high based on lower bound
        if self.low < self.min_value:

            # calculate how much the new low is below lower bound
            overage = self.min_value - self.low

            # add overage to high
            self.high += overage

            # if new high is above upper bound, set it to max
            if self.high > self.max_value:
                self.high = self.max_value

            # set low to lower bound
            self.low = self.min_value

        # adjust high and low based on upper bound
        if self.high > self.max_value:

            # calculate how much the new high is above upper bound
            overage = self.high - self.max_value

            # subtract overage from low
            self.low -= overage

            # if new low is below lower bound, set it to lower bound
            if self.low < self.min_value:
                self.low = self.min_value

            # set high to upper bound
            self.high = self.max_value

    def set_low_high(self,
                     new_low: float,
                     new_high: float):
        """Update low and high values directly"""
        self.low = new_low
        self.high = new_high

    def format_bounds(self) -> str:
        """Format bounds as string"""
        return f"[{round_sig(self.min_value)},{round_sig(self.max_value)}]"

    def format_range(self) -> str:
        """Format range as string"""
        return f"[{round_sig(self.low)},{round_sig(self.high)}]"

    def __str__(self) -> str:
        """String representation of the parameter range"""
        return f"Parameter '{self.name}': bounds={self.format_bounds()}, current range={self.format_range()}"
