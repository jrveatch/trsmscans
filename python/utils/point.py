
# standard libraries
import logging
from typing import Dict, Optional

# local modules
from utils.math_utils import round_sig
from utils.model import Model

# class that holds parameter and xb values for a single point
class Point:

    # initialize point parameters
    def __init__(self,
                 model: Model,
                 par_vals: Optional[Dict[str,float]] = None,
                 xb: float = 0.0):

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # store model name
        self.__model = model

        # initialize parameter values to 0.0 if a model is provided
        self.__input_parameter_values = {par: 0.0 for par in model.input_parameter_names}
        self.__output_parameter_values = {par: 0.0 for par in model.output_parameter_names}
        self.__width_parameter_values = {par: 0.0 for par in model.width_parameter_names}

        # if par_vals is provided, update the parameter values
        if par_vals is not None:
            self.update_parameter_values(par_vals)
        else:
            self.logger.debug("No parameter values provided, using default values.")

        # store xb value
        self.xb = xb

    @property
    def model(self) -> Optional[Model]:
        """The model object"""
        return self.__model

    @property
    def input_parameter_values(self) -> Dict[str,float]:
        """Dictionary of input parameter values"""
        return self.__input_parameter_values

    @property
    def output_parameter_values(self) -> Dict[str,float]:
        """Dictionary of output parameter values"""
        return self.__output_parameter_values

    @property
    def width_parameter_values(self) -> Dict[str,float]:
        """Dictionary of width parameter values"""
        return self.__width_parameter_values

    # Combined view (read-only)
    @property
    def parameter_values(self):
        return {
            **self.input_parameter_values,
            **self.output_parameter_values,
            **self.width_parameter_values,
        }

    # Method to update existing keys only
    def update_parameter_values(self, updates: dict):
        for key, value in updates.items():
            if key in self.__input_parameter_values:
                self.__input_parameter_values[key] = value
            elif key in self.__output_parameter_values:
                self.__output_parameter_values[key] = value
            elif key in self.__width_parameter_values:
                self.__width_parameter_values[key] = value

    def copy(self, new_xb: Optional[float] = None) -> 'Point':
        """Return a copy of the point with a new xb value"""
        if new_xb is None:
            new_xb = self.xb
        return Point(model=self.model, par_vals=self.parameter_values, xb=new_xb)

    # wrapper function to get attribute
    def get_val(self,
                varname: str) -> float:
        # if xb is requested, return it
        if varname == "xb":
            return self.xb
        # otherwise return value from parameter_values
        try:
            return self.parameter_values[varname]
        except KeyError:
            raise KeyError(f"Parameter '{varname}' not found in this point.")

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
        return Point(model=self.model, par_vals=self.parameter_values, xb=self.xb*scale_factor)

    def __str__(self) -> str:
        return f"{self.xb}\n{self.parameter_values}"

    def __repr__(self) -> str:
        return f"{self.xb}\n{self.parameter_values}"
