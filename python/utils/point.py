
# local modules
from utils.math_utils import round_sig
from utils.model import Model

# class that holds parameter and xb values for a single point
class Point:

    # initialize point parameters
    def __init__(self,
                 model_name: str,
                 par_vals: dict[str,float] = {},
                 xb: float = 0.0):

        # store model name
        self.__model_name = model_name

        # initialize empty dictionary of parameter values
        self.__par_vals: dict[str,float] = {}

        # if par_vals exists, store it
        if par_vals:
            self.__par_vals = par_vals
        # otherwise create default dictionary from model
        else:
            self.__par_vals = {par: 0.0 for par in Model(self.__model_name).parameter_names}

        # store xb value
        self.xb = xb

    @property
    def model_name(self) -> str:
        """Name of the model"""
        return self.__model_name
    
    @property
    def par_vals(self) -> dict[str,float]:
        """Dictionary of parameter values"""
        return self.__par_vals

    # wrapper function to get attribute
    def get_val(self,
                varname: str) -> float:
        # if xb is requested, return it
        if varname == "xb":
            return self.xb
        # otherwise return value from par_vals
        else:
            return self.__par_vals[varname]

    # get difference between two values of varname
    def diff(self,
             other: 'Point',
             par_name: str) -> float:
        return self.get_val(par_name) - other.get_val(par_name)

    # get fractional difference between two values of varname
    def diff_frac(self,
                  other: 'Point',
                  par_name: str) -> float:
        abs_val = abs(self.get_val(par_name))
        if abs_val < 1e-13:
            return 1.0
        return self.diff(other,par_name) / abs_val

    # get formatted string of xb
    def format_xb(self) -> str:
        return f"{self.xb:.2E}"

    # get formatted string of parameter
    def format_param(self,
                     par_name: str) -> str:
        return f"{round_sig(self.get_val(par_name))}"

    # get formatted string of parameter diff w.r.t. another point
    def format_diff(self,
                    other: 'Point',
                    par_name: str) -> str:
        return f"{round_sig(self.diff(other,par_name))}"

    # get formatted string of parameter fractional diff w.r.t. another point
    def format_diff_frac(self,
                         other: 'Point',
                         par_name: str) -> str:
        return f"{self.diff_frac(other,par_name):1.2f}"

    # define the greater than (>) operator
    def __gt__(self,other: 'Point'):
        return self.xb > other.xb

    # define the greater than or equal to (>=) operator
    def __ge__(self,other: 'Point'):
        return self.xb >= other.xb

    # define the less than (<) operator
    def __lt__(self,other: 'Point'):
        return self.xb < other.xb

    # define the less than or equal to (<=) operator
    def __le__(self,other: 'Point'):
        return self.xb <= other.xb

    # multiply a point's xb by a float and return a new point
    def __mul__(self,scale_factor: float):
        return Point(self.__model_name, self.__par_vals, self.xb*scale_factor)

    def __str__(self) -> str:
        return f"{self.xb}\n{self.__par_vals}"

    def __repr__(self) -> str:
        return f"{self.xb}\n{self.__par_vals}"
