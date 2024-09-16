from typing import Any, Optional

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,
                 name: str,
                 dict: dict[str, Any]):

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

    # get name
    def name(self) -> str:
        return self.__name

    # get low
    def get_low(self) -> float:
        return self.__low

    # get high
    def get_high(self) -> float:
        return self.__high

    # get lower bound
    def get_lower_bound(self) -> float:
        return self.__lower_bound

    # get upper bound
    def get_upper_bound(self) -> float:
        return self.__upper_bound

    # get fullname
    def get_fullname(self) -> str:
        return self.__fullname

    # get precision
    def get_precision(self) -> int:
        return self.__precision

    # get the parameter center given current low and high
    def center(self) -> float:
        return (self.__low + self.__high) / 2
    
    # get range (inclusive)
    def range(self) -> tuple:
        return (self.__low, self.__high)

    # get range given current low and high
    def width(self) -> float:
        return abs(self.__high - self.__low)

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # this also sets new range values

    def set_lower_bound(self,
                        newMin: float) -> None:
        self.__lower_bound = newMin
        if self.__low < self.__lower_bound:
            self.__low = self.__lower_bound

    def set_upper_bound(self,
                        newMax: float) -> None:
        self.__upper_bound = newMax
        if self.__high > self.__upper_bound:
            self.__high = self.__upper_bound
    
    # set new value, range, low and high
    def scale_width(self,
                    newVal: Optional[float] = None,
                    rangeScale: float = 1.0) -> None:

        # if both newVal is None and rangeScale is 1.0, complain and return existing low
        if newVal is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        width = self.width()

        # scale width by given value
        width *= rangeScale

        # find new low and high using the half width
        self.__low = self.center() - width / 2
        self.__high = self.center() + width / 2

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

    # update the low to a new value
    def set_low(self, value: float) -> None:

        if value < self.__lower_bound:
            # restrict low if outside bound
            self.__low = self.__lower_bound
        else:
            # update low to our new value
            self.__low = value
    
    # update the high to a new value
    def set_high(self, value: float) -> None:

        if value > self.__upper_bound:
            # restrict high if outside bound
            self.__high = self.__upper_bound
        else:
            # update high to our new value
            self.__high = value

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
