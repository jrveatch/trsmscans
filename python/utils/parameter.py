
# standard libraries
import logging
from typing import Any, Optional

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
        self.__precision = dict['precision']
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
    def precision(self) -> int:
        """Precision of the parameter"""
        return self.__precision

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
                    newVal: Optional[float] = None,
                    rangeScale: float = 1.0) -> None:

        # if both newVal is None and rangeScale is 1.0, complain and return existing low
        if newVal is None and rangeScale == 1.0:
            self.logger.warning("Attempting to update parameter with no new information... returning...")
            return

        width = self.width
        center = self.center

        # scale width by given value
        width *= rangeScale

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

    # print min and max
    def print_bounds(self) -> None:
        print(self.__name + ": ["+f"{self.__lower_bound:1.{self.__precision}f}"+","+f"{self.__upper_bound:1.{self.__precision}f}"+"]")

    # get formatted string showing range
    def format_range(self) -> str:
        string_range = "range = ["
        string_range += f"{self.__low:1.{self.__precision}f}"
        string_range += ","
        string_range += f"{self.__high:1.{self.__precision}f}"
        string_range += "]"
        return string_range
