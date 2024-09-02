
# import model class to initialize Point class
from utils.model import Model

# import decimal class for nicely formatted strings
from decimal import Decimal

# class that holds parameter and xb values for a single point
class Point:

    # initialize point parameters
    def __init__(self,
                 model_name: str,
                 parvals: dict[str,float] = {},
                 xb: float = 0.0):
        
        # get model
        self.model = Model(model_name)

        # initialize empty dictionary
        self.parvals: dict[str,float] = {}

        # if parvals exists, store it
        if parvals:
            self.parvals = parvals
        # otherwise create default dictionary from model
        else:
            # get list of parameters from model
            parlist = self.model.parameter_names()

            # loop over list of parameters and make default dictionary
            for par in parlist:
                self.parvals[par] = 0.0

        # store xb value
        self.xb = xb

    # wrapper function to get attribute
    def get_val(self,
                varname: str) -> float:
        # if xb is requested, return it
        if varname == "xb":
            return self.xb
        # otherwise return value from parvals
        else:
            return self.parvals[varname]

    # get difference between two values of varname
    def diff(self,
             other: 'Point',
             parname: str) -> float:
        return self.get_val(parname) - other.get_val(parname)

    # get fractional difference between two values of varname
    # TODO: Add divide-by-zero protection
    def diff_frac(self,
                  other: 'Point',
                  parname: str) -> float:
        return self.diff(other,parname) / abs(self.get_val(parname))
    
    # get formatted string of xb
    def format_xb(self) -> str:
        return f"{Decimal(self.xb):.3E}"
    
    # get formatted string of parameter
    def format_param(self,
                     parname: str) -> str:
        return "value = " + f"{self.get_val(parname):1.{self.model.parameter(parname)['precision']}f}"
    
    # get formatted string of parameter diff w.r.t. another point
    def format_diff(self,
                    other: 'Point',
                    parname: str) -> str:
        return "diff. = " + f"{self.diff(other,parname):1.{self.model.parameter(parname)['precision']}f}"
    
    # get formatted string of parameter fractional diff w.r.t. another point
    def format_diff_frac(self,
                         other: 'Point',
                         parname: str) -> str:
        return "rel. diff. = " + f"{self.diff_frac(other,parname):1.2f}"

    # define the greater than (>) operator
    def __gt__(self,other: 'Point'):
        return self.xb > other.xb

    # define the less than (<) operator
    def __lt__(self,other: 'Point'):
        return self.xb < other.xb
