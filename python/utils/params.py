
# standard libraries
import logging
from typing import Optional

# local modules
from utils.masses import Masses
from utils.model import Model
from utils.parameter import Parameter
from utils.point import Point

# class to hold and update full set of parameters used in a scan
class Params:

    def __init__(self,
                 model_name: str,
                 masses: 'Masses',
                 decay: str = ""):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # store masses
        self.__masses = masses

        # set H1/2/3 mass values
        self.__mH1 = masses.mH1
        self.__mH2 = masses.mH2
        self.__mH3 = masses.mH3

        # get model using model_name
        self.__model = Model(model_name)

        # Store model and decay names
        self.__model_name = model_name
        self.__decay = decay

        # get list of parameter names
        self.__parameter_names: list[str] = self.__model.parameter_names

        # create dictionary of parameters
        self.__parameters: dict[str,'Parameter'] = {}
        for name in self.__parameter_names:
            self.__parameters[name] = Parameter(name,self.__model.parameter(name))

    ## Class properties

    @property
    def parameters(self) -> dict[str, Parameter]:
        """Dictionary of parameters"""
        return self.__parameters

    @property
    def parameter_names(self) -> list[str]:
        """List of parameter name"""
        return self.__parameter_names

    @property
    def masses(self) -> Masses:
        """Masses used in run"""
        return self.__masses

    @property
    def model_name(self) -> str:
        """Name of model being used"""
        return self.__model_name

    @property
    def decay(self) -> str:
        """Decay mode being used"""
        return self.__decay

    ## Calculated values

    # get parameter from dict
    def parameter_value(self,
                        par_name: str) -> Parameter:
        return self.__parameters[par_name]

    def center_points(self) -> tuple[float]:
        return tuple([param.center() for param in self.__parameters.values()])
    
    def ranges(self) -> tuple[tuple[float]]:
        return tuple([param.range() for param in self.__parameters.values()])

    def widths(self) -> tuple[float]:
        return tuple([param.width() for param in self.__parameters.values()])

    # get starting min value from model
    def starting_min(self,
                     par_name: str) -> float:
        return self.__model.starting_min(par_name)

    # get starting max value from model
    def starting_max(self,
                     par_name: str) -> float:
        return self.__model.starting_max(par_name)

    # set new value, range, low and high
    def scale_ranges(self,
                     newPoint: Optional[Point] = None,
                     rangeScale: float = 1.0) -> None:

        # if both newPoint is None and rangeScale is 1.0, complain and return existing low
        if newPoint is None and rangeScale == 1.0:
            self.logger.warning("Attempting to update parameter with no new information... returning...")
            return

        # loop over parameters
        for par_name in self.__parameter_names:

            # initialize new value to be None
            newVal = None

            # if new point is provided, get new value from it
            if newPoint:
                newVal = newPoint.get_val(par_name)

            # update parameter with new value and range scale
            self.__parameters[par_name].scale_width(newVal=newVal,
                                                   rangeScale=rangeScale)

    # change bounds of each parameter based on new center point
    def reposition_center(self, point: tuple[float]):
        for (center, param) in zip(point, self.__parameters.values()):
            extent = param.width() / 2

            param.set_low_high(center - extent, center + extent)

    # update both low and high of each parameter using dictionaries
    def update_low_high(self,
                        low_dict: dict = None,
                        high_dict: dict = None) -> None:

        # check to see if low_dict exists
        if low_dict is not None:

            # loop over parameters
            for par_name, new_low in low_dict.items():
                if par_name in self.__parameters:
                    # use low_dict to update the low for each parameter
                    self.__parameters[par_name].low = new_low
                else:
                    self.logger.warning(f"{par_name} is not known")
            
        # check to see if high_dict exists
        if high_dict is not None:

            # loop over parameters
            for par_name, new_high in high_dict.items():
                if par_name in self.__parameters:
                    # use high_dict to update the high for each parameter
                    self.__parameters[par_name].high = new_high
                else:
                    self.logger.warning(f"{par_name} is not known")

    # function to calculate volume of parameter space
    def volume(self) -> float:

        # initialize volume to 1
        volume = 1.0

        # loop over parameters
        for par in self.__parameters.values():
        
            # make sure range is non-zero
            if par.width > 1e-13:
        
                # multiply volume by parameter range
                volume *= par.width
        
        return volume
    
    # function to write .ini file with parameters
    def write_ini(self,
                  ini_name: str) -> None:

        # read in template .ini file
        template = open(self.__model.template_ini,"r")
        ini_data = template.read()
        template.close()

        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.__mH1))
        ini_data = ini_data.replace("MH2",str(self.__mH2))
        ini_data = ini_data.replace("MH3",str(self.__mH3))

        # loop over parameters and fill low/high values
        for par in self.parameters.values():
            ini_data = ini_data.replace(par.name+"_LOW",str(par.low))
            ini_data = ini_data.replace(par.name+"_HIGH",str(par.high))

        # write to .ini file
        outfile = open(ini_name,"w")
        outfile.write(ini_data)
        outfile.close()

    ## Aliases

    # Alias for self.center_point()
    @property
    def vol_position(self) -> tuple[float]:
        return self.center_points()

    # Alias for self.widths()
    @property
    def vol_width(self) -> tuple[float]:
        return self.widths()

    # Alias for self.ranges()
    @property
    def vol_range(self) -> tuple[tuple[float, float]]:
        return self.ranges()

    # parameter name indexing
    def __getitem__(self, key) -> Parameter:
        return self.parameter_value(key)

    ## FIXME: ! below not tested ! note: should be about right, but will need to update later on if bug

    # initialize iteration
    def __iter__(self):
        self.__iter_idx = -1
        return self
    
    # get next value
    def __next__(self):
        self.__iter_idx += 1

        if self.__iter_idx >= len(self.__parameters):
            raise StopIteration
        
        return list(self.__parameters.values())[self.__iter_idx]
    
    # length of params
    def __len__(self):
        return len(self.__parameters)
