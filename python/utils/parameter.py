
# standard libraries
import logging
from typing import Any, Dict, Optional

# local modules
from utils.math_utils import round_sig

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,
                 name: str,
                 bounds_dict: Dict[str, Any]):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize parameter name
        self.__name = name

        # initialize values from dictionary
        self.__min_value = bounds_dict['min']
        self.__max_value = bounds_dict['max']

        # initialize low and high from lower and upper bounds
        self.__low = self.__min_value
        self.__high = self.__max_value

    @property
    def name(self) -> str:
        """Name of the parameter"""
        return self.__name

    @property
    def low(self) -> float:
        """Low value of the parameter"""
        return self.__low

    @low.setter
    def low(self,
            new_low: float) -> None:
        if new_low < self.__min_value:
            """Restrict low if outside bound"""
            self.__low = self.__min_value
        else:
            """Update to new value"""
            self.__low = new_low

    @property
    def high(self) -> float:
        """High value of the parameter"""
        return self.__high
    
    @high.setter
    def high(self,
             new_high: float) -> None:
        if new_high > self.__max_value:
            """Restrict high if outside bound"""
            self.__high = self.__max_value
        else:
            """Update to new value"""
            self.__high = new_high

    @property
    def min_value(self) -> float:
        """Minimum value of the parameter"""
        return self.__min_value

    @min_value.setter
    def min_value(self,
                    new_min_value: float) -> None:
        self.__min_value = new_min_value
        """If current low is less than minimum value, adjust it"""
        if self.__low < self.__min_value:
            self.__low = self.__min_value

    @property
    def max_value(self) -> float:
        """Maximum value of the parameter"""
        return self.__max_value

    @max_value.setter
    def max_value(self,
                    new_max_value: float) -> None:
        self.__max_value = new_max_value
        """If current high is greater than minimum value, adjust it"""
        if self.__high > self.__max_value:
            self.__high = self.__max_value

    @property
    def center(self) -> float:
        """Center value of the parameter"""
        return (self.__low + self.__high) / 2
    
    @property
    def range(self) -> tuple:
        """High and low values of the parameter"""
        return (self.__low, self.__high)

    @property
    def width(self) -> float:
        """Width of the parameter"""
        return abs(self.__high - self.__low)

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

        # find new low and high using the half width
        self.__low = center - width / 2
        self.__high = center + width / 2

        # adjust low and high based on lower bound
        if self.__low < self.__min_value:
            
            # calculate how much the new low is below lower bound
            overage = self.__min_value - self.__low

            # add overage to high
            self.__high += overage

            # if new high is above upper bound, set it to max
            if self.__high > self.__max_value:
                self.__high = self.__max_value

            # set low to lower bound
            self.__low = self.__min_value

        # adjust high and low based on upper bound
        if self.__high > self.__max_value:

            # calculate how much the new high is above upper bound
            overage = self.__high - self.__max_value

            # subtract overage from low
            self.__low -= overage

            # if new low is below lower bound, set it to lower bound
            if self.__low < self.__min_value:
                self.__low = self.__min_value
            
            # set high to upper bound
            self.__high = self.__max_value

        return

    def set_low_high(self,
                     new_low: float,
                     new_high: float):
        """Update low and high values directly"""
        self.low = new_low
        self.high = new_high

    def format_bounds(self) -> str:
        """Format bounds as string"""
        return f"[{round_sig(self.__min_value)},{round_sig(self.__max_value)}]"

    def format_range(self) -> str:
        """Format range as string"""
        return f"[{round_sig(self.__low)},{round_sig(self.__high)}]"
