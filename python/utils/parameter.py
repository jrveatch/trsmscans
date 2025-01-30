
# standard libraries
import logging
from typing import Any, Optional

# local modules
from utils.math_utils import round_sig

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,
                 name: str,
                 dict: dict[str, Any]):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # initialize parameter name
        self.__name = name

        # initialize values from dictionary
        self.__fullname = dict['fullname']
        self.__lower_bound = dict['min']
        self.__upper_bound = dict['max']

        # initialize low and high from lower and upper bounds
        self.__low = self.__lower_bound
        self.__high = self.__upper_bound

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
        if new_low < self.__lower_bound:
            """Restrict low if outside bound"""
            self.__low = self.__lower_bound
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
        if new_high > self.__upper_bound:
            """Restrict high if outside bound"""
            self.__high = self.__upper_bound
        else:
            """Update to new value"""
            self.__high = new_high

    @property
    def lower_bound(self) -> float:
        """Lower bound of the parameter"""
        return self.__lower_bound

    @lower_bound.setter
    def lower_bound(self,
                    new_lower_bound: float) -> None:
        self.__lower_bound = new_lower_bound
        """If current low is less than lower bound, adjust it"""
        if self.__low < self.__lower_bound:
            self.__low = self.__lower_bound

    @property
    def upper_bound(self) -> float:
        """Upper bound of the parameter"""
        return self.__upper_bound

    @upper_bound.setter
    def upper_bound(self,
                    new_upper_bound: float) -> None:
        self.__upper_bound = new_upper_bound
        """If current high is greater than lower bound, adjust it"""
        if self.__high > self.__upper_bound:
            self.__high = self.__upper_bound

    @property
    def fullname(self) -> str:
        """Full name of the parameter"""
        return self.__fullname

    @property
    def center(self) -> float:
        """Center value of the parameter"""
        return (self.__low + self.__high) / 2
    
    @property
    def range(self) -> tuple:
        """Range value of the parameter"""
        return (self.__low, self.__high)

    @property
    def width(self) -> float:
        """Width value of the parameter"""
        return abs(self.__high - self.__low)
    
    # set new value, range, low and high
    def scale_width(self,
                    new_val: Optional[float] = None,
                    range_scale: float = 1.0) -> None:

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
        if self.__low < self.__lower_bound:
            
            # calculate how much the new low is below lower bound
            overage = self.__lower_bound - self.__low

            # add overage to high
            self.__high += overage

            # if new high is above upper bound, set it to max
            if self.__high > self.__upper_bound:
                self.__high = self.__upper_bound

            # set low to lower bound
            self.__low = self.__lower_bound

        # adjust high and low based on upper bound
        if self.__high > self.__upper_bound:

            # calculate how much the new high is above upper bound
            overage = self.__high - self.__upper_bound

            # subtract overage from low
            self.__low -= overage

            # if new low is below lower bound, set it to lower bound
            if self.__low < self.__lower_bound:
                self.__low = self.__lower_bound
            
            # set high to upper bound
            self.__high = self.__upper_bound

        return

    # update both low and high values
    def set_low_high(self,
                     new_low: float,
                     new_high: float):
        self.low = new_low
        self.high = new_high

    # format bounds as string
    def format_bounds(self) -> str:
        return f"[{round_sig(self.__lower_bound)},{round_sig(self.__upper_bound)}]"

    # get range as string
    def format_range(self) -> str:
        return f"[{round_sig(self.__low)},{round_sig(self.__high)}]"
