
# standard libraries
import logging
import random
from typing import Any, Dict, Optional, Tuple

# local modules
from utils.math_utils import round_sig

# class to hold and update ranges for a single model parameter
class ParamRange:
    """
    Represents the tunable range and bounds for a single model parameter.

    This class tracks the full range (min/max bounds) and the current working range
    (low/high) used during parameter space scans. It provides methods for
    scaling, clamping, sampling, and formatting the range.

    Typical use cases include:
    - Managing ranges within a ParamSpace for scanning
    - Generating random samples within the current range
    - Adjusting bounds during adaptive scans or optimization passes
    """

    def __init__(self,
                 name: str,
                 param_info: Dict[str, Any]):
        """
        Initializes a ParamRange for a single parameter.

        Args:
            name (str): Short name of the parameter.
            param_info (Dict[str, Any]): Dictionary containing 'fullname', 'min', and 'max'.
        """

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
        """Returns the short name of the parameter."""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Sets the short name of the parameter."""
        self.__name = new_name

    @property
    def full_name(self) -> str:
        """Returns the full name of the parameter."""
        return self.__full_name

    @full_name.setter
    def full_name(self,
                  new_full_name: str) -> None:
        """Sets the full name of the parameter."""
        self.__full_name = new_full_name

    @property
    def low(self) -> float:
        """Returns the low value of the current parameter range."""
        return self.__low

    @low.setter
    def low(self,
            new_low: float) -> None:
        """Sets the low value of the parameter range, clamped to the minimum allowed value."""
        self.__low = new_low
        if new_low < self.min_value:
            self.__low = self.min_value

    @property
    def high(self) -> float:
        """Returns the high value of the current parameter range."""
        return self.__high

    @high.setter
    def high(self,
             new_high: float) -> None:
        """Sets the high value of the parameter range, clamped to the maximum allowed value."""
        self.__high = new_high
        if new_high > self.max_value:
            self.__high = self.max_value

    @property
    def min_value(self) -> float:
        """Returns the absolute minimum value permitted for the parameter."""
        return self.__min_value

    @min_value.setter
    def min_value(self,
                  new_min_value: float) -> None:
        self.__min_value = new_min_value
        """Sets the minimum allowed value for the parameter and clamps the current low value if needed."""
        if hasattr(self, '_ParamRange__low'):
            if self.low < self.min_value:
                self.low = self.min_value
        else:
            self.__low = self.__min_value

    @property
    def max_value(self) -> float:
        """Returns the absolute maximum value permitted for the parameter."""
        return self.__max_value

    @max_value.setter
    def max_value(self,
                  new_max_value: float) -> None:
        self.__max_value = new_max_value
        """Sets the maximum allowed value for the parameter and clamps the current high value if needed."""
        if hasattr(self, '_ParamRange__high'):
            if self.high > self.max_value:
                self.high = self.max_value
        else:
            self.__high = self.__max_value

    @property
    def center(self) -> float:
        """Returns the midpoint between the current low and high values."""
        return (self.low + self.high) / 2

    @property
    def range(self) -> Tuple[float, float]:
        """Returns a tuple (low, high) representing the current parameter range."""
        return (self.low, self.high)

    @property
    def width(self) -> float:
        """Returns the width (high - low) of the current parameter range."""
        return abs(self.high - self.low)

    def scale_width(self,
                    new_val: Optional[float] = None,
                    range_scale: float = 1.0) -> None:
        """
        Scales the current range around the center by a given factor.

        If the new range exceeds the min or max bounds, it is clamped accordingly.

        Args:
            new_val (Optional[float]): Ignored in current implementation (placeholder).
            range_scale (float): Scaling factor for the range width.
        """

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
                     new_high: float) -> None:
        """
        Sets both the low and high values of the parameter range.

        Args:
            new_low (float): New low value.
            new_high (float): New high value.
        """
        self.low = new_low
        self.high = new_high

    def set_min_max(self,
                    new_min: float,
                    new_max: float,
                    resolution: float = 0.01) -> None:
        """
        Updates min and max bounds with a small buffer relative to total width.

        Args:
            new_min (float): Proposed new minimum value.
            new_max (float): Proposed new maximum value.
            resolution (float): Relative buffer size as a fraction of total width.
        """

        buffer = abs(self.max_value - self.min_value) * resolution
        if new_min > self.min_value + buffer:
            self.min_value = new_min - buffer
        if new_max < self.max_value - buffer:
            self.max_value = new_max + buffer

    def random_point(self) -> float:
        """
        Generates a random float uniformly sampled within the current parameter range.

        Returns:
            float: A random value between low and high.
        """
        return random.uniform(self.low, self.high)

    def format_bounds(self) -> str:
        """
        Returns a formatted string of the min and max bounds.

        Returns:
            str: A string like "[100,200]".
        """
        return f"[{round_sig(self.min_value)},{round_sig(self.max_value)}]"

    def format_range(self) -> str:
        """
        Returns a formatted string of the current range (low to high).

        Returns:
            str: A string like "[120,180]".
        """
        return f"[{round_sig(self.low)},{round_sig(self.high)}]"

    def __str__(self) -> str:
        """
        Returns a string representation of the parameter including bounds and range.

        Returns:
            str: Descriptive string summarizing the parameter state.
        """
        return f"Parameter '{self.name}': bounds={self.format_bounds()}, current range={self.format_range()}"
