
from masses import Masses
from utils.model import Model
from utils.point import Point

from typing import Optional, Dict

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
        self.__parnames = self.__model.parameter_names()

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
    def parnames(self):
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

    def set_min(self,
                parname: str,
                newMin: float) -> None:
        self.parameter(parname).set_min(newMin)

    def set_max(self,
                parname: str,
                newMax: str) -> None:
        self.parameter(parname).set_max(newMax)

    # function to calculate parameter value
    def get_midpoint(self,
                    low: float,
                    high: float) -> float:
        return (low + high) / 2

    # function to calculate parameter ranges
    def get_range(self,
                  low: float,
                  high: float) -> float:
        return abs(high - low) / 2

    # set new value, range, low and high
    def update_params(self,
                      newPoint: Optional[Point] = None,
                      rangeScale: float = 1.0):

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
            self.__parameters[parname].update_param(newVal=newVal,
                                                    rangeScale=rangeScale)

    # function to calculate volume of parameter space
    def volume(self) -> float:

        # initialize volume to 1
        volume = 1.0

        # loop over parameters
        for par in self.__parameters.values():
        
            # make sure range is non-zero
            if par.range() > 1e-13:
        
                # multiply volume by parameter range
                volume *= par.range()
        
        return volume

    # function to get min value
    def min(self,
            parname: str) -> float:
        return self.parameter(parname).min()

    # function to get max value
    def max(self,
            parname: str) -> float:
        return self.parameter(parname).max()

    # function to get low value
    def low(self,
            parname: str) -> float:
        return self.parameter(parname).low()

    # function to get high value
    def high(self,
             parname: str) -> float:
        return self.parameter(parname).high()
    
    # function to get parameter values
    def val(self,
            parname: str) -> float:
        return self.parameter(parname).val()
    
    # function to get parameter ranges
    def range(self,
              parname: str) -> range:
        return self.parameter(parname).range()
    
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
            ini_data = ini_data.replace(par.name()+"_LOW",str(par.low()))
            ini_data = ini_data.replace(par.name()+"_HIGH",str(par.high()))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(ini_data)
        outfile.close()

    # print min and max for a parameter
    def print_min_max(self,
                      parname: str) -> None:
        self.parameter(parname).print_min_max()

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,name,dict):

        # initialize parameter name
        self.__name = name

        # initialize values from dictionary
        self.__fullname = dict['fullname']
        self.__precision = dict['precision']
        self.__min = dict['min']
        self.__max = dict['max']

        # initialize low and high from min and max
        self.__low = self.__min
        self.__high = self.__max

        # initialize value as the midpoint
        self.__val = self.get_midpoint()

        # initialize range
        self.__range = self.get_range()

    # get name
    def name(self) -> str:
        return self.__name

    # get low
    def low(self) -> float:
        return self.__low

    # get high
    def high(self) -> float:
        return self.__high

    # get range
    def range(self) -> float:
        return self.__range

    # get min
    def min(self) -> float:
        return self.__min

    # get max
    def max(self) -> float:
        return self.__max

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

    def set_min(self,newMin):
        self.__min = newMin
        if self.__low < self.__min:
            self.__low = self.__min
            self.__range = self.get_range()

    def set_max(self,newMax):
        self.__max = newMax
        if self.__high > self.__max:
            self.__high = self.__max
            self.__range = self.get_range()
    
    # set new value, range, low and high
    def update_param(self,
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

        # adjust low and high based on min
        if self.__low < self.__min:
            
            # calculate how much the new low is below min
            overage = self.__min - self.__low

            # add overage to high
            self.__high += overage

            # if new high is above max, set it to max
            if self.__high > self.__max:
                self.__high = self.__max

            # set low to min
            self.__low = self.__min

        # adjust high and low based on max
        if self.__high > self.__max:

            # calculate how much the new high is above max
            overage = self.__high - self.__max

            # subtract overage from low
            self.__low -= overage

            # if new low is below min, set it to min
            if self.__low < self.__min:
                self.__low = self.__min
            
            # set high to max
            self.__high = self.__max

        return

    # print min and max
    def print_min_max(self):
        print(self.__name + ": ["+f"{self.__min:1.{self.__precision}f}"+","+f"{self.__max:1.{self.__precision}f}"+"]")

    # get formatted string showing range
    def format_range(self):
        string_range = "range = ["
        string_range += f"{self.__low:1.{self.__precision}f}"
        string_range += ","
        string_range += f"{self.__high:1.{self.__precision}f}"
        string_range += "]"
        return string_range
