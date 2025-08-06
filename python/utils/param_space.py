
# standard libraries
import copy
from functools import cached_property
from typing import Dict, List, Optional, Tuple

# local modules
from utils.logging_utils import log_table
from utils.model import Model
from utils.param_range import ParamRange
from utils.point import Point

# get logger
import logging
logger = logging.getLogger(__name__)

# class to hold and update full set of parameter ranges used in a scan
class ParamSpace:
    """
    Represents a scan space defined over a model's input parameters.

    ParamSpace manages a collection of ParamRange objects corresponding to each input
    parameter defined by a given model. It supports operations such as random point
    generation, center-point evaluation, scaling or repositioning of the space, and
    writing .ini files for external scan tools. It also tracks the scalar masses and
    decay mode used in the context of the scan.

    Typical use cases include:
    - Defining parameter ranges for ScannerS or optimization routines.
    - Dynamically adjusting bounds based on scan results.
    - Generating initial points or splitting the space for refinement.
    """

    def __init__(self,
                 model: Model,
                 decay: str = "NoDecay",
                 name: str = "Default"):
        """
        Initializes a ParamSpace representing a space defined over model input parameters.

        Args:
            model (Model): The model object providing parameter definitions.
            decay (str): The decay mode used for scan analysis.
            name (str): A label for the parameter space instance.
        """

        # get model using model_name
        self.__model = model

        # Store decay name
        self.__decay = decay

        self.__name = name

    ## Class properties

    @property
    def name(self) -> str:
        """Returns the name of the parameter space."""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Sets the name of the parameter space."""
        self.__name = new_name

    @cached_property
    def mH1(self) -> float:
        """Returns the mass of the lightest scalar (H1)."""
        return self.model.get_mass("H1")

    @cached_property
    def mH2(self) -> float:
        """Returns the mass of the second-lightest scalar (H2)."""
        return self.model.get_mass("H2")

    @cached_property
    def mH3(self) -> float:
        """Returns the mass of the heaviest scalar (H3)."""
        return self.model.get_mass("H3")

    @cached_property
    def parameter_ranges(self) -> Dict[str, ParamRange]:
        """Returns a dictionary mapping parameter names to ParamRange objects."""
        return {name: ParamRange(name, self.model.input_parameter(name))
                for name in self.parameter_names}

    @property
    def parameter_names(self) -> Tuple[str, ...]:
        """Returns a tuple of names of all input parameters."""
        return self.model.input_parameter_names

    @property
    def mass_string(self) -> str:
        """Returns a string encoding scalar masses (e.g., 'X400_S150')."""
        return self.model.mass_string

    @property
    def model_name(self) -> str:
        """Returns the name of the associated model."""
        return self.model.name

    @property
    def model(self) -> Model:
        """Returns the Model object associated with this parameter space."""
        return self.__model

    @property
    def decay(self) -> str:
        """Returns the decay mode being used in the scan."""
        return self.__decay

    def center_point(self) -> Point:
        """Returns a Point object at the center of the current parameter ranges."""
        return Point(model=self.model,
                     par_vals={name:self.parameter_ranges[name].center for name in self.parameter_names})

    def random_point(self) -> Point:
        """Returns a randomly sampled Point within the parameter ranges."""
        return Point(model=self.model,
                     par_vals={name:self.parameter_ranges[name].random_point() for name in self.parameter_names})

    def ranges(self) -> Tuple[Tuple[float, float], ...]:
        """Returns a tuple of (low, high) pairs for all parameters."""
        return tuple([param_range.range for param_range in self.parameter_ranges.values()])

    def widths(self) -> Tuple[float, ...]:
        """Returns a tuple of range widths for all parameters."""
        return tuple([param_range.width for param_range in self.parameter_ranges.values()])

    def starting_min(self,
                     par_name: str) -> float:
        """
        Returns the model's initial minimum value for a parameter.

        Args:
            par_name (str): Parameter name.

        Returns:
            float: Initial minimum.
        """
        return self.model.starting_min(par_name)

    def starting_max(self,
                     par_name: str) -> float:
        """
        Returns the model's initial maximum value for a parameter.

        Args:
            par_name (str): Parameter name.

        Returns:
            float: Initial maximum.
        """
        return self.model.starting_max(par_name)

    def scale_ranges(self,
                     new_point: Optional[Point] = None,
                     range_scale: float = 1.0) -> None:
        """
        Scales all parameter ranges around a new center point or the current center.

        Args:
            new_point (Optional[Point]): Optional center point to recenter ranges.
            range_scale (float): Factor to scale the current widths.
        """

        # complain and exit if there is nothing to do
        if new_point is None and range_scale == 1.0:
            logger.warning("Attempting to update parameter with no new information... returning...")
            return

        # loop over parameters
        for par_name in self.parameter_names:

            # initialize new value to be None
            new_val = None

            # if new point is provided, get new value from it
            if new_point:
                new_val = new_point.get_val(par_name)

            # update parameter with new value and range scale
            self.parameter_ranges[par_name].scale_width(new_val=new_val,
                                                        range_scale=range_scale)

    def reposition_center(self, point: Point) -> None:
        """
        Re-centers all parameter ranges around the values in the given Point.

        Args:
            point (Point): Point containing new center values.
        """

        for name, center in point.input_parameter_values.items():
            if name in self.parameter_ranges:
                param_range = self.parameter_ranges[name]
                width = param_range.width / 2
                logger.debug(f"Updating parameter '{name}' range to ({center - width},{center + width})")
                param_range.set_low_high(center - width, center + width)
            else:
                logger.debug(f"Skipping parameter '{name}' since it is not in the parameter ranges")

    def update_low_high(self,
                        low_dict: Optional[Dict[str, float]] = None,
                        high_dict: Optional[Dict[str, float]] = None) -> None:
        """
        Updates low/high bounds for parameters from the given dictionaries.

        Args:
            low_dict (Optional[Dict[str, float]]): New low bounds by parameter.
            high_dict (Optional[Dict[str, float]]): New high bounds by parameter.
        """

        # check to see if low_dict exists
        if low_dict is not None:

            # loop over parameters
            for par_name, new_low in low_dict.items():
                if par_name in self.parameter_ranges:
                    # use low_dict to update the low for each parameter
                    self.parameter_ranges[par_name].low = new_low
                else:
                    logger.warning(f"{par_name} is not known")

        # check to see if high_dict exists
        if high_dict is not None:

            # loop over parameters
            for par_name, new_high in high_dict.items():
                if par_name in self.parameter_ranges:
                    # use high_dict to update the high for each parameter
                    self.parameter_ranges[par_name].high = new_high
                else:
                    logger.warning(f"{par_name} is not known")

    def volume(self) -> float:
        """
        Computes the volume of the parameter space (product of widths).

        Returns:
            float: The volume of the space.
        """
        # initialize volume to 1
        volume = 1.0
        # loop over parameters
        for param_range in self.parameter_ranges.values():
            # make sure range is non-zero
            if param_range.width > 1e-13:
                # multiply volume by parameter range
                volume *= param_range.width
        return volume

    def write_ini(self,
                  ini_name: str) -> None:
        """
        Writes a filled .ini file using the template and current parameter ranges.

        Args:
            ini_name (str): Output file path for the .ini file.
        """

        print(f"Writing ini to {ini_name}")

        # read in template .ini file
        with open(self.model.template_ini,"r") as template:
            ini_data = template.read()

        print(f'ini_data: {ini_data}')
        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.mH1))
        ini_data = ini_data.replace("MH2",str(self.mH2))
        ini_data = ini_data.replace("MH3",str(self.mH3))

        # loop over parameters and fill low/high values
        for param_range in self.parameter_ranges.values():
            ini_data = ini_data.replace(param_range.name+"_LOW",str(param_range.low))
            ini_data = ini_data.replace(param_range.name+"_HIGH",str(param_range.high))

        print(ini_data)

        # write to .ini file
        with open(ini_name,"w") as outfile:
            outfile.write(ini_data)

    def split_range(self,
                    param_name: str,
                    split_values: List[float]) -> List['ParamSpace']:
        """
        Splits the parameter range of a single parameter into subspaces.

        Args:
            param_name (str): Parameter to split.
            split_values (List[float]): List of split points within the range.

        Returns:
            List[ParamSpace]: A list of new ParamSpace instances with split ranges.

        Raises:
            ValueError: If split points are out of bounds or parameter name is invalid.
        """

        if param_name not in self.parameter_ranges:
            raise ValueError(f"Parameter '{param_name}' not found in Params object")

        # Ensure sorted and unique split points
        split_points = sorted(set(split_values))

        # Get original parameter range
        param = self.parameter_ranges[param_name]
        low = param.low
        high = param.high

        # Check that all split points are within the original range
        for val in split_points:
            if not (low < val < high):
                raise ValueError(
                    f"Split value {val} is outside the range of parameter '{param_name}' "
                    f"({low}, {high})"
                )

        # Include endpoints to create full range intervals
        all_bounds = [low, *split_points, high]

        # Create deep copies for each split
        split_params_list = []
        for i in range(len(all_bounds) - 1):
            p = copy.deepcopy(self)
            p.name = p.name + str(i)
            p.parameter_ranges[param_name].set_low_high(all_bounds[i], all_bounds[i+1])
            split_params_list.append(p)

        return split_params_list

    def log_bounds_table(self) -> None:
        """Logs a table of parameter names and their min/max bounds."""
        # make list of headers for parameter bounds table and empty list of rows
        headers = ["Parameter", "Bounds"]
        rows = []

        # loop over parameters and add to rows
        for parameter_name in self.parameter_names:
            # add parameter name and bounds to rows
            rows.append([parameter_name, self.parameter_ranges[parameter_name].format_bounds()])

        # print table of parameter bounds
        log_table(logger=logger,
                  headers=headers,
                  rows=rows)

    def log_range_table(self) -> None:
        """Logs a table of parameter names and their current low/high range."""
        # make list of headers for parameter bounds table and empty list of rows
        headers = ["Parameter", "Range"]
        rows = []

        # loop over parameters and add to rows
        for parameter_name in self.parameter_names:
            # add parameter name and bounds to rows
            rows.append([parameter_name, self.parameter_ranges[parameter_name].format_range()])

        # print table of parameter bounds
        log_table(logger=logger,
                  headers=headers,
                  rows=rows)

    def __getitem__(self, key) -> ParamRange:
        """
        Allows dictionary-style access to parameter ranges.

        Args:
            key (str): Parameter name.

        Returns:
            ParamRange: The corresponding parameter range.
        """
        return self.parameter_ranges[key]

    def __iter__(self):
        """Enables iteration over the ParamRange objects in the space."""
        return iter(self.parameter_ranges.values())

    def __str__(self) -> str:
        """
        Returns a string summary of the parameter space configuration.

        Returns:
            str: Multi-line string with name, model, decay, and parameter states.
        """

        lines = [f"Params object {self.name} for model: {self.model_name}, decay: {self.decay}"]
        for name in self.parameter_names:
            param = self.parameter_ranges[name]
            lines.append(str(param))  # uses ParamRange.__str__
        return "\n".join(lines) + "\n"
