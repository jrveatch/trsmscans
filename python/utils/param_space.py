
# standard libraries
import copy
from functools import cached_property
import logging
from typing import Dict, List, Optional, Tuple

# local modules
from utils.logging_utils import log_table
from utils.model import Model
from utils.param_range import ParamRange
from utils.point import Point

# class to hold and update full set of parameter ranges used in a scan
class ParamSpace:

    def __init__(self,
                 model: Model,
                 decay: str = "NoDecay",
                 name: str = "Default"):

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # get model using model_name
        self.__model = model

        # Store decay name
        self.__decay = decay

        self.__name = name

    ## Class properties

    @property
    def name(self) -> str:
        """Name of the parameter space"""
        return self.__name

    @name.setter
    def name(self,
             new_name: str) -> None:
        """Set the name property"""
        self.__name = new_name

    @cached_property
    def mH1(self) -> float:
        """Mass of H1"""
        return self.model.get_mass("H1")

    @cached_property
    def mH2(self) -> float:
        """Mass of H2"""
        return self.model.get_mass("H2")

    @cached_property
    def mH3(self) -> float:
        """Mass of H3"""
        return self.model.get_mass("H3")

    @cached_property
    def parameter_ranges(self) -> Dict[str, ParamRange]:
        """Dictionary of parameter ranges"""
        return {name: ParamRange(name, self.model.input_parameter(name))
                for name in self.parameter_names}

    @property
    def parameter_names(self) -> Tuple[str]:
        """Tuple of parameter name"""
        return self.model.input_parameter_names

    @property
    def mass_string(self) -> str:
        """Mass string"""
        return self.model.mass_string

    @property
    def model_name(self) -> str:
        """Name of model being used"""
        return self.model.name

    @property
    def model(self) -> Model:
        """Model object"""
        return self.__model

    @property
    def decay(self) -> str:
        """Decay mode being used"""
        return self.__decay

    def center_point(self) -> Point:
        """Get center point for parameter space"""
        return Point(model=self.model,
                     par_vals={name:self.parameter_ranges[name].center for name in self.parameter_names})

    def random_point(self) -> Point:
        """Get random point within parameter space"""
        return Point(model=self.model,
                     par_vals={name:self.parameter_ranges[name].random_point() for name in self.parameter_names})

    def ranges(self) -> Tuple[Tuple[float]]:
        """Get tuple of ranges for parameters"""
        return tuple([param_range.range for param_range in self.parameter_ranges.values()])

    def widths(self) -> Tuple[float]:
        """Get tuple of widths for parameters"""
        return tuple([param_range.width for param_range in self.parameter_ranges.values()])

    def starting_min(self,
                     par_name: str) -> float:
        """Get starting min value for a parameter"""
        return self.model.starting_min(par_name)

    def starting_max(self,
                     par_name: str) -> float:
        """Get starting max value for a parameter"""
        return self.model.starting_max(par_name)

    def scale_ranges(self,
                     new_point: Optional[Point] = None,
                     range_scale: float = 1.0) -> None:
        """Set new central value, range, low and high for all parameters"""

        # complain and exit if there is nothing to do
        if new_point is None and range_scale == 1.0:
            self.logger.warning("Attempting to update parameter with no new information... returning...")
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
        """Change low and high of parameter ranges around a new center point"""
        for name, center in point.input_parameter_values.items():
            if name in self.parameter_ranges:
                param_range = self.parameter_ranges[name]
                width = param_range.width / 2
                self.logger.debug(f"Updating parameter '{name}' range to ({center - width},{center + width})")
                param_range.set_low_high(center - width, center + width)
            else:
                self.logger.debug(f"Skipping parameter '{name}' since it is not in the parameter ranges")

    def update_low_high(self,
                        low_dict: Optional[Dict[str, float]] = None,
                        high_dict: Optional[Dict[str, float]] = None) -> None:
        """Update low and high of all parameter ranges from dictionary"""

        # check to see if low_dict exists
        if low_dict is not None:

            # loop over parameters
            for par_name, new_low in low_dict.items():
                if par_name in self.parameter_ranges:
                    # use low_dict to update the low for each parameter
                    self.parameter_ranges[par_name].low = new_low
                else:
                    self.logger.warning(f"{par_name} is not known")

        # check to see if high_dict exists
        if high_dict is not None:

            # loop over parameters
            for par_name, new_high in high_dict.items():
                if par_name in self.parameter_ranges:
                    # use high_dict to update the high for each parameter
                    self.parameter_ranges[par_name].high = new_high
                else:
                    self.logger.warning(f"{par_name} is not known")

    def volume(self) -> float:
        """Calculate the volume of the parameter space defined"""
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
        """Write .ini files with parameter ranges"""

        # read in template .ini file
        with open(self.model.template_ini,"r") as template:
            ini_data = template.read()

        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.mH1))
        ini_data = ini_data.replace("MH2",str(self.mH2))
        ini_data = ini_data.replace("MH3",str(self.mH3))

        # loop over parameters and fill low/high values
        for param_range in self.parameter_ranges.values():
            ini_data = ini_data.replace(param_range.name+"_LOW",str(param_range.low))
            ini_data = ini_data.replace(param_range.name+"_HIGH",str(param_range.high))

        # write to .ini file
        with open(ini_name,"w") as outfile:
            outfile.write(ini_data)

    def split_range(self,
                    param_name: str,
                    split_values: List[float]) -> List['ParamSpace']:
        """Create new Params objects by splitting one parameter range at the specified values"""
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
        all_bounds = [low] + split_points + [high]

        # Create deep copies for each split
        split_params_list = []
        for i in range(len(all_bounds) - 1):
            p = copy.deepcopy(self)
            p.name = p.name + str(i)
            p.parameter_ranges[param_name].set_low_high(all_bounds[i], all_bounds[i+1])
            split_params_list.append(p)

        return split_params_list

    def log_bounds_table(self) -> None:
        """Log the bounds of all parameters in a table format"""
        # make list of headers for parameter bounds table and empty list of rows
        headers = ["Parameter", "Bounds"]
        rows = []

        # loop over parameters and add to rows
        for parameter_name in self.parameter_names:
            # add parameter name and bounds to rows
            rows.append([parameter_name, self.parameter_ranges[parameter_name].format_bounds()])

        # print table of parameter bounds
        log_table(logger=self.logger,
                  headers=headers,
                  rows=rows)

    def log_range_table(self) -> None:
        """Log the range of all parameters in a table format"""
        # make list of headers for parameter bounds table and empty list of rows
        headers = ["Parameter", "Range"]
        rows = []

        # loop over parameters and add to rows
        for parameter_name in self.parameter_names:
            # add parameter name and bounds to rows
            rows.append([parameter_name, self.parameter_ranges[parameter_name].format_range()])

        # print table of parameter bounds
        log_table(logger=self.logger,
                  headers=headers,
                  rows=rows)

    ## Aliases

    # Alias for self.center_point()
    @property
    def vol_position(self) -> Point:
        return self.center_point()

    # Alias for self.widths()
    @property
    def vol_width(self) -> Tuple[float]:
        return self.widths()

    def __getitem__(self, key) -> ParamRange:
        """Return the ParamRange object corresponding to `par_name`"""
        return self.parameter_ranges[key]

    def __iter__(self):
        """Define iterator over parameter values"""
        return iter(self.parameter_ranges.values())

    def __str__(self) -> str:
        """String representation of all parameters"""
        lines = [f"Params object {self.name} for model: {self.model_name}, decay: {self.decay}"]
        for name in self.parameter_names:
            param = self.parameter_ranges[name]
            lines.append(str(param))  # uses ParamRange.__str__
        return "\n".join(lines) + "\n"
