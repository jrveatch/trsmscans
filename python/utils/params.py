
# standard libraries
import logging
from typing import Dict, Optional, Tuple

# local modules
from utils.model import Model
from utils.parameter import Parameter
from utils.point import Point

# class to hold and update full set of parameters used in a scan
class Params:

    def __init__(self,
                 model: 'Model',
                 decay: str = "NoDecay"):

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # get model using model_name
        self.__model = model

        # set H1/2/3 mass values
        self.__mH1 = model.get_mass("H1")
        self.__mH2 = model.get_mass("H2")
        self.__mH3 = model.get_mass("H3")

        # Store decay name
        self.__decay = decay

        # get tuple of parameter names
        self.__parameter_names: Tuple[str] = self.model.input_parameter_names

        # create dictionary of parameters
        self.__parameters = {
            name: Parameter(name, self.__model.input_parameter(name))
            for name in self.__parameter_names
            }

    ## Class properties

    @property
    def mH1(self) -> float:
        """Mass of H1"""
        return self.__mH1

    @property
    def mH2(self) -> float:
        """Mass of H2"""
        return self.__mH2

    @property
    def mH3(self) -> float:
        """Mass of H3"""
        return self.__mH3

    @property
    def parameters(self) -> Dict[str, Parameter]:
        """Dictionary of parameters"""
        return self.__parameters

    @property
    def parameter_names(self) -> Tuple[str]:
        """Tuple of parameter name"""
        return self.__parameter_names

    @property
    def mass_string(self) -> str:
        """Mass string"""
        return self.__model.mass_string

    @property
    def model_name(self) -> str:
        """Name of model being used"""
        return self.__model.name

    @property
    def model(self) -> 'Model':
        """Model object"""
        return self.__model

    @property
    def decay(self) -> str:
        """Decay mode being used"""
        return self.__decay

    def parameter_value(self,
                        par_name: str) -> Parameter:
        """Get parameter from dictionary"""
        return self.parameters[par_name]

    def center_points(self) -> Tuple[float]:
        """Get tuple of center points for parameters"""
        return tuple([param.center for param in self.parameters.values()])

    def ranges(self) -> Tuple[Tuple[float]]:
        """Get tuple of ranges for parameters"""
        return tuple([param.range for param in self.parameters.values()])

    def widths(self) -> Tuple[float]:
        """Get tuple of widths for parameters"""
        return tuple([param.width for param in self.parameters.values()])

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
            self.parameters[par_name].scale_width(new_val=new_val,
                                                  range_scale=range_scale)

    def reposition_center(self, point: Tuple[float]):
        """Change low and high of parameters around a new center point"""
        for (center, param) in zip(point, self.parameters.values()):
            width = param.width / 2
            param.set_low_high(center - width, center + width)

    def update_low_high(self,
                        low_dict: Optional[Dict[str, float]] = None,
                        high_dict: Optional[Dict[str, float]] = None) -> None:
        """Update low and high of all parameters from dictionary"""

        # check to see if low_dict exists
        if low_dict is not None:

            # loop over parameters
            for par_name, new_low in low_dict.items():
                if par_name in self.parameters:
                    # use low_dict to update the low for each parameter
                    self.parameters[par_name].low = new_low
                else:
                    self.logger.warning(f"{par_name} is not known")

        # check to see if high_dict exists
        if high_dict is not None:

            # loop over parameters
            for par_name, new_high in high_dict.items():
                if par_name in self.parameters:
                    # use high_dict to update the high for each parameter
                    self.parameters[par_name].high = new_high
                else:
                    self.logger.warning(f"{par_name} is not known")

    def volume(self) -> float:
        """Calculate the volume of the parameter space defined"""
        # initialize volume to 1
        volume = 1.0
        # loop over parameters
        for par in self.parameters.values():
            # make sure range is non-zero
            if par.width > 1e-13:
                # multiply volume by parameter range
                volume *= par.width
        return volume

    def write_ini(self,
                  ini_name: str) -> None:
        """Write .ini files with parameter values"""

        # read in template .ini file
        with open(self.model.template_ini,"r") as template:
            ini_data = template.read()

        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.mH1))
        ini_data = ini_data.replace("MH2",str(self.mH2))
        ini_data = ini_data.replace("MH3",str(self.mH3))

        # loop over parameters and fill low/high values
        for par in self.parameters.values():
            ini_data = ini_data.replace(par.name+"_LOW",str(par.low))
            ini_data = ini_data.replace(par.name+"_HIGH",str(par.high))

        # write to .ini file
        with open(ini_name,"w") as outfile:
            outfile.write(ini_data)

    ## Aliases

    # Alias for self.center_point()
    @property
    def vol_position(self) -> Tuple[float]:
        return self.center_points()

    # Alias for self.widths()
    @property
    def vol_width(self) -> Tuple[float]:
        return self.widths()

    # Alias for self.ranges()
    @property
    def vol_range(self) -> Tuple[Tuple[float, float]]:
        return self.ranges()

    def __getitem__(self, key) -> Parameter:
        """Return the Parameter object corresponding to `par_name`."""
        return self.parameter_value(key)

    def __iter__(self):
        """Define iterator over parameter values"""
        return iter(self.parameters.values())
