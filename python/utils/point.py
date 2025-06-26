
# standard libraries
from functools import cached_property
from typing import Dict, Optional

# third-party libraries
import pandas as pd

# local modules
from utils.math_utils import round_sig
from utils.model import Model

# get logger
import logging
logger = logging.getLogger(__name__)

# class that holds parameter and xb values for a single point
class Point:
    """
    Represents a single point in the parameter space of a model scan.

    Holds input/output/width parameter values, scalar masses, and an `xb` value
    (e.g., cross-section * branching ratio). Supports reading/writing `.ini` files,
    arithmetic operations, and comparisons based on `xb`.
    """

    def __init__(self,
                 model: Model,
                 par_vals: Optional[Dict[str,float]] = None,
                 xb: float = 0.0,
                 tsv_data: Optional[pd.DataFrame] = None):
        """
        Initializes a Point with a model and optionally specific parameter values and xb.

        Args:
            model (Model): The model defining the parameter structure.
            par_vals (Optional[Dict[str, float]]): Dictionary of parameter values. If None, all set to 0.
            xb (float): The xb value associated with this point (default is 0.0).
        """

        # store model name
        self.__model = model

        # initialize parameter values to 0.0 if a model is provided
        self.__input_parameter_values = dict.fromkeys(model.input_parameter_names, 0.0)
        self.__output_parameter_values = dict.fromkeys(model.output_parameter_names, 0.0)
        self.__width_parameter_values = dict.fromkeys(model.width_parameter_names, 0.0)

        # if par_vals is provided, update the parameter values
        if par_vals is not None:
            self.update_parameter_values(par_vals)
        else:
            logger.debug("No parameter values provided, using default values.")

        # store xb value
        self.xb = xb

        # store tsv data if provided
        if tsv_data is not None:
            self.__tsv_data = tsv_data
        else:
            self.__tsv_data = pd.DataFrame()

    @property
    def model(self) -> Model:
        """Returns the model associated with this point."""
        return self.__model

    @property
    def model_name(self) -> str:
        """Returns the name of the model."""
        return self.model.name

    @cached_property
    def mH1(self) -> float:
        """Returns the mass of scalar H1."""
        return self.model.get_mass("H1")

    @cached_property
    def mH2(self) -> float:
        """Returns the mass of scalar H2."""
        return self.model.get_mass("H2")

    @cached_property
    def mH3(self) -> float:
        """Returns the mass of scalar H3."""
        return self.model.get_mass("H3")

    @property
    def input_parameter_values(self) -> Dict[str,float]:
        """Returns a dictionary of input parameter values."""
        return self.__input_parameter_values

    @property
    def output_parameter_values(self) -> Dict[str,float]:
        """Returns a dictionary of output parameter values."""
        return self.__output_parameter_values

    @property
    def width_parameter_values(self) -> Dict[str,float]:
        """Returns a dictionary of width parameter values."""
        return self.__width_parameter_values

    @property
    def parameter_values(self) -> Dict[str,float]:
        """Returns a combined read-only dictionary of all parameter values (input, output, width)."""
        return {
            **self.input_parameter_values,
            **self.output_parameter_values,
            **self.width_parameter_values,
        }

    @property
    def tsv_data(self) -> pd.DataFrame:
        """
        Returns a DataFrame with the point's information from the .tsv file.
        """
        return self.__tsv_data

    @tsv_data.setter
    def tsv_data(self, __new_tsv_data: pd.DataFrame) -> None:
        """
        Sets the .tsv data for this point.

        Args:
            __new_tsv_data (pd.DataFrame): DataFrame containing the point's information.
        """
        if not isinstance(__new_tsv_data, pd.DataFrame):
            raise TypeError("tsv_data must be a pandas DataFrame.")
        self.__tsv_data = __new_tsv_data

    def update_parameter_values(self,
                                updates: Dict[str,float]) -> None:
        """
        Updates existing parameter values from a dictionary.

        Only keys already present in the input/output/width parameter dicts will be updated.

        Args:
            updates (Dict[str,float]): Dictionary of parameter names and new values.
        """

        for key, value in updates.items():
            if key in self.__input_parameter_values:
                self.__input_parameter_values[key] = value
            elif key in self.__output_parameter_values:
                self.__output_parameter_values[key] = value
            elif key in self.__width_parameter_values:
                self.__width_parameter_values[key] = value

    def copy(self,
             new_xb: Optional[float] = None) -> 'Point':
        """
        Returns a new copy of the point with the same parameters and optionally a new xb value.

        Args:
            new_xb (Optional[float]): New xb value (defaults to current xb).

        Returns:
            Point: A copy of this point.
        """

        if new_xb is None:
            new_xb = self.xb
        return Point(model=self.model, par_vals=self.parameter_values, xb=new_xb)

    def get_val(self,
                varname: str) -> float:
        """
        Gets the value of a parameter or 'xb'.

        Args:
            varname (str): Parameter name or 'xb'.

        Returns:
            float: The corresponding value.

        Raises:
            KeyError: If the parameter name is invalid.
        """

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
        """
        Computes the difference in a parameter value between two points.

        Args:
            other (Point): The other point to compare with.
            par_name (str): The parameter to compare.

        Returns:
            float: Difference in values.
        """
        return self.get_val(par_name) - other.get_val(par_name)

    def diff_frac(self,
                  other: 'Point',
                  par_name: str) -> float:
        """
        Computes the fractional difference in a parameter between two points.

        Args:
            other (Point): The other point to compare.
            par_name (str): The parameter name.

        Returns:
            float: Fractional difference. Returns 1.0 if the base value is near zero.
        """
        abs_val = abs(self.get_val(par_name))
        if abs_val < 1e-13:
            return 1.0
        return self.diff(other,par_name) / abs_val

    def write_ini(self,
                  ini_name: str) -> None:
        """
        Writes an .ini file based on this point's parameter values.

        Args:
            ini_name (str): Output file path.
        """

        # read in template .ini file
        with open(self.model.template_ini,"r") as template:
            ini_data = template.read()

        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.mH1))
        ini_data = ini_data.replace("MH2",str(self.mH2))
        ini_data = ini_data.replace("MH3",str(self.mH3))

        # loop over parameters and fill low/high values
        for name, value in self.input_parameter_values.items():
            ini_data = ini_data.replace(name+"_LOW",str(value))
            ini_data = ini_data.replace(name+"_HIGH",str(value))

        # write to .ini file
        with open(ini_name,"w") as outfile:
            outfile.write(ini_data)

    def format_xb(self) -> str:
        """Returns a formatted string representation of the xb value."""
        return f"{self.xb:.2E}"

    def format_param(self,
                     par_name: str) -> str:
        """
        Returns a formatted string of a parameter's value.

        Args:
            par_name (str): The parameter name.

        Returns:
            str: Rounded string.
        """
        return f"{round_sig(self.get_val(par_name))}"

    def format_diff(self,
                    other: 'Point',
                    par_name: str) -> str:
        """
        Returns a formatted string of the difference in a parameter between two points.

        Args:
            other (Point): The point to compare.
            par_name (str): The parameter name.

        Returns:
            str: Rounded difference string.
        """
        return f"{round_sig(self.diff(other,par_name))}"

    def format_diff_frac(self,
                         other: 'Point',
                         par_name: str) -> str:
        """
        Returns a formatted string of the fractional difference between two points.

        Args:
            other (Point): The point to compare.
            par_name (str): Parameter name.

        Returns:
            str: Formatted fractional difference.
        """
        return f"{self.diff_frac(other,par_name):1.2f}"

    def write_tsv_to_file(self,
                          tsv_name: str) -> None:
        """
        Writes the point's .tsv data to a file.

        Args:
            tsv_name (str): Output file path.
        """
        if self.tsv_data.empty:
            logger.warning("No .tsv data available to write.")
            return
        self.tsv_data.to_csv(tsv_name,
                             sep="\t",
                             index=True,
                             mode='a',
                             header=False)

    def __gt__(self,other: 'Point') -> bool:
        """Returns True if this point's xb is greater (>) than the other's."""
        return self.xb > other.xb

    def __ge__(self,other: 'Point') -> bool:
        """Returns True if this point's xb is greater than or equal (>=) to the other's."""
        return self.xb >= other.xb

    def __lt__(self,other: 'Point') -> bool:
        """Returns True if this point's xb is less (<) than the other's."""
        return self.xb < other.xb

    def __le__(self,other: 'Point') -> bool:
        """Returns True if this point's xb is less than or equal (<=) to the other's."""
        return self.xb <= other.xb

    # multiply a point's xb by a float and return a new point
    def __mul__(self,
                scale_factor: float) -> 'Point':
        """
        Multiplies the xb value by a scalar and returns a new Point with the result.

        Args:
            scale_factor (float): Scalar to multiply xb by.

        Returns:
            Point: New Point with scaled xb.
        """
        return Point(model=self.model, par_vals=self.parameter_values, xb=self.xb*scale_factor)

    def __str__(self) -> str:
        """Returns a concise string with xb and parameter values."""
        return f"{self.xb}\n{self.parameter_values}"

    def __repr__(self) -> str:
        """Returns a developer-friendly string representation of the Point."""
        return f"{self.xb}\n{self.parameter_values}"
