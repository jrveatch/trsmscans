
from utils.masses import Masses
from utils.model import Model
from utils.point import Point
from utils.parameter import Parameter

from typing import Optional

# class to hold and update full set of parameters used in a scan
class Params:

    def __init__(self,
                 model_name: str,
                 masses: 'Masses'):

        # store masses
        self.__masses = masses

        # set H1/2/3 mass values
        self.__mH1 = masses.mH1
        self.__mH2 = masses.mH2
        self.__mH3 = masses.mH3

        # get model using model_name
        self.__model = Model(model_name)

        # get list of parameter names
        self.__parameter_names: list[str] = self.__model.parameter_names()

        # create dictionary of parameters
        self.__parameters: dict[str,'Parameter'] = {}
        for par in self.__parameter_names:
            self.__parameters[par] = Parameter(par,self.__model.parameter(par))

    # get dictionary of parameters
    def parameters(self) -> dict[str,'Parameter']:
        return self.__parameters

    # get parameter
    def parameter(self,
                  par_name: str) -> 'Parameter':
        return self.__parameters[par_name]

    # get parameter names
    def parameter_names(self) -> list[str]:
        return self.__parameter_names

    # get masses
    def masses(self) -> 'Masses':
        return self.__masses
    
    def midpoint_tuples(self) -> tuple[float]:
        return tuple([param.get_midpoint() for param in self.__parameters.values()])
    
    def extent_tuples(self) -> tuple[tuple[float]]:
        return tuple([(param.get_low(), param.get_high()) for param in self.__parameters.values()])

    # get starting min value from model
    def starting_min(self,
                     par_name: str) -> float:
        return self.__model.starting_min(par_name)

    # get starting max value from model
    def starting_max(self,
                     par_name: str) -> float:
        return self.__model.starting_max(par_name)
    
    # get model name
    def model_name(self) -> str:
        return self.__model.name()

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # these also set new range values

    def set_lower_bound(self,
                        par_name: str,
                        newMin: float) -> None:
        self.parameter(par_name).set_lower_bound(newMin)

    def set_upper_bound(self,
                        par_name: str,
                        newMax: str) -> None:
        self.parameter(par_name).set_upper_bound(newMax)

    # set new value, range, low and high
    def scale_ranges(self,
                     newPoint: Optional[Point] = None,
                     rangeScale: float = 1.0) -> None:

        # if both newPoint is None and rangeScale is 1.0, complain and return existing low
        if newPoint is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        # loop over parameters
        for par_name in self.__parameter_names:

            # initialize new value to be None
            newVal = None

            # if new point is provided, get new value from it
            if newPoint:
                newVal = newPoint.get_val(par_name)

            # update parameter with new value and range scale
            self.__parameters[par_name].scale_range(newVal=newVal,
                                                   rangeScale=rangeScale)

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
                    self.__parameters[par_name].update_low(new_low)
                else:
                    print(f"Warning: {par_name} is not known")
            
        # check to see if high_dict exists
        if high_dict is not None:

            # loop over parameters
            for par_name, new_high in high_dict.items():
                if par_name in self.__parameters:
                    # use high_dict to update the high for each parameter
                    self.__parameters[par_name].update_high(new_high)
                else:
                    print(f"Warning: {par_name} is not known")

    # function to calculate volume of parameter space
    def volume(self) -> float:

        # initialize volume to 1
        volume = 1.0

        # loop over parameters
        for par in self.__parameters.values():
        
            # make sure range is non-zero
            if par.get_range() > 1e-13:
        
                # multiply volume by parameter range
                volume *= par.get_range()
        
        return volume

    # function to get lower bound value
    def lower_bound(self,
                    par_name: str) -> float:
        return self.parameter(par_name).lower_bound()

    # function to get max value
    def upper_bound(self,
                    par_name: str) -> float:
        return self.parameter(par_name).upper_bound()

    # function to get low value
    def get_low(self,
                par_name: str) -> float:
        return self.parameter(par_name).get_low()

    # function to get high value
    def get_high(self,
                 par_name: str) -> float:
        return self.parameter(par_name).get_high()
    
    # function to get parameter ranges
    def range(self,
              par_name: str) -> float:
        return self.parameter(par_name).get_range()
    
    # function to write .ini file with parameters
    def write_ini(self,
                  ini_name: str) -> None:

        # read in template .ini file
        template = open(self.__model.template_ini(),"r")
        ini_data = template.read()
        template.close()

        # create ini_data with parameters
        ini_data = ini_data.replace("MH1",str(self.__mH1))
        ini_data = ini_data.replace("MH2",str(self.__mH2))
        ini_data = ini_data.replace("MH3",str(self.__mH3))

        # loop over parameters and fill low/high values
        for par in self.parameters().values():
            ini_data = ini_data.replace(par.name()+"_LOW",str(par.get_low()))
            ini_data = ini_data.replace(par.name()+"_HIGH",str(par.get_high()))

        # write to .ini file
        outfile = open(ini_name,"w")
        outfile.write(ini_data)
        outfile.close()

    # print min and max for a parameter
    def print_bounds(self,
                     par_name: str) -> None:
        self.parameter(par_name).print_bounds()
