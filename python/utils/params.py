
from utils.masses import Masses
from utils.model import Model
from utils.point import Point

from typing import Optional, Dict, List

# class to hold and update full set of parameters used in a scan
class Params:

    def __init__(self,
                 modelname: str,
                 masses: 'Masses'):

        # store masses
        self.__masses = masses

        # set H1/2/3 mass values
        self.__mH1 = masses.mH1
        self.__mH2 = masses.mH2
        self.__mH3 = masses.mH3

        # get model using modelname
        self.__model = Model(modelname)

        # get list of parameter names
        self.__parnames: List[str] = self.__model.parameter_names()

        # create dictionary of parameters
        self.__parameters: Dict[str,'Parameter'] = {}
        for par in self.__parnames:
            self.__parameters[par] = Parameter(par,self.__model.parameter(par))

    # get dictionary of parameters
    def parameters(self) -> Dict[str,'Parameter']:
        return self.__parameters

    # get parameter
    def parameter(self,
                  parname: str) -> 'Parameter':
        return self.__parameters[parname]

    # get parameter names
    def parnames(self) -> List[str]:
        return self.__parnames

    # get masses
    def masses(self) -> 'Masses':
        return self.__masses

    # get starting min value from model
    def starting_min(self,
                     parname: str) -> float:
        return self.__model.starting_min(parname)

    # get starting max value from model
    def starting_max(self,
                     parname: str) -> float:
        return self.__model.starting_max(parname)
    
    # get model name
    def model_name(self) -> str:
        return self.__model.name()

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # these also set new range values

    def set_lower_bound(self,
                        parname: str,
                        newMin: float) -> None:
        self.parameter(parname).set_lower_bound(newMin)

    def set_upper_bound(self,
                        parname: str,
                        newMax: str) -> None:
        self.parameter(parname).set_upper_bound(newMax)

    # set new value, range, low and high
    def scale_ranges(self,
                     newPoint: Optional[Point] = None,
                     rangeScale: float = 1.0) -> None:

        # if both newPoint is None and rangeScale is 1.0, complain and return existing low
        if newPoint is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        # loop over parameters
        for parname in self.__parnames:

            # initialize new value to be None
            newVal = None

            # if new point is provided, get new value from it
            if newPoint:
                newVal = newPoint.get_val(parname)

            # update parameter with new value and range scale
            self.__parameters[parname].scale_range(newVal=newVal,
                                                   rangeScale=rangeScale)

    # update both low and high of each parameter using dictionaries
    def update_low_high(self,
                        lowdict:dict=None,
                        highdict:dict=None) -> None:

        # check to see if lowdict exists
        if lowdict is not None:

            # loop over parameters
            for parname, newlow in lowdict.items():
                if parname in self.__parameters:
                    # use lowdict to update the low for each parameter
                    self.__parameters[parname].update_low(newlow)
                else:
                    print(f"Warning: {parname} is not known")
            
        # check to see if highdict exists
        if highdict is not None:

            # loop over parameters
            for parname, newhigh in highdict.items():
                if parname in self.__parameters:
                    # use highdict to update the high for each parameter
                    self.__parameters[parname].update_high(newhigh)
                else:
                    print(f"Warning: {parname} is not known")

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
                    parname: str) -> float:
        return self.parameter(parname).lower_bound()

    # function to get max value
    def upper_bound(self,
                    parname: str) -> float:
        return self.parameter(parname).upper_bound()

    # function to get low value
    def get_low(self,
                parname: str) -> float:
        return self.parameter(parname).get_low()

    # function to get high value
    def get_high(self,
                 parname: str) -> float:
        return self.parameter(parname).get_high()
    
    # function to get parameter ranges
    def range(self,
              parname: str) -> range:
        return self.parameter(parname).get_range()
    
    # function to write .ini file with parameters
    def write_ini(self,
                  ininame: str) -> None:

        # read in template .ini file
        template = open(self.__model.template_ini(),"r")
        ini_data = template.read()
        template.close()

        # create inidata with parameters
        ini_data = ini_data.replace("MH1",str(self.__mH1))
        ini_data = ini_data.replace("MH2",str(self.__mH2))
        ini_data = ini_data.replace("MH3",str(self.__mH3))

        # loop over parameters and fill low/high values
        for par in self.parameters().values():
            ini_data = ini_data.replace(par.name()+"_LOW",str(par.get_low()))
            ini_data = ini_data.replace(par.name()+"_HIGH",str(par.get_high()))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(ini_data)
        outfile.close()

    # print min and max for a parameter
    def print_bounds(self,
                     parname: str) -> None:
        self.parameter(parname).print_bounds()

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,name,dict):

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

        # initialize value as the midpoint
        self.__val = self.get_midpoint()

        # initialize range
        self.__range = self.get_range()

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
    def lower_bound(self) -> float:
        return self.__lower_bound

    # get upper bound
    def upper_bound(self) -> float:
        return self.__upper_bound

    # get fullname
    def fullname(self) -> str:
        return self.__fullname

    # get precision
    def precision(self) -> int:
        return self.__precision

    # get the midpoint given current low and high
    def get_midpoint(self) -> float:
        return (self.__low + self.__high) / 2

    # get range given current low and high
    def get_range(self) -> float:
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
            self.__range = self.get_range()

    def set_upper_bound(self,
                        newMax: float) -> None:
        self.__upper_bound = newMax
        if self.__high > self.__upper_bound:
            self.__high = self.__upper_bound
            self.__range = self.get_range()
    
    # set new value, range, low and high
    def scale_range(self,
                    newVal: Optional[float] = None,
                    rangeScale: float = 1.0) -> None:

        # if both newVal is None and rangeScale is 1.0, complain and return existing low
        if newVal is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        # if a new val is given, update stored val
        if newVal:
            self.__val = newVal

        # scale range by given value
        self.__range *= rangeScale

        # find new low and high using the half range
        self.__low = self.__val - self.__range / 2
        self.__high = self.__val + self.__range / 2

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
    def update_low(self,
                   newval: float) -> None:

        # check if newval is higher than previous low
        if newval < self.__lower_bound:
            self.set_low(self.__lower_bound)
            return

        # update low to our newval
        self.set_low(newval)
    
    # update the high to a new value
    def update_high(self,
                    newval: float) -> None:

        # check if newval is lower than previous high
        if newval > self.__upper_bound:
            self.set_high(self.__upper_bound)
            return

        # update high to our newval
        self.set_high(newval)

    # set the new low and update the range to reflect the new low
    def set_low(self,
                newval: float) -> None:
        self.__low = newval
        self.range = self.get_range()

    def set_high(self,
                 newval: float) -> None:
        self.__high = newval
        self.range = self.get_range()

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
