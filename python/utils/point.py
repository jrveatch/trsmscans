
# local modules
from utils.model import Model

# class that holds parameter and xb values for a single point
class Point:

    # initialize point parameters
    def __init__(self,
                 model_name: str,
                 par_vals: dict[str,float] = {},
                 xb: float = 0.0):
        
        # get model
        self.model = Model(model_name)

        # initialize empty dictionary
        self.par_vals: dict[str,float] = {}

        # if par_vals exists, store it
        if par_vals:
            self.par_vals = par_vals
        # otherwise create default dictionary from model
        else:
            # get list of parameters from model
            par_list = self.model.parameter_names()

            # loop over list of parameters and make default dictionary
            for par in par_list:
                self.par_vals[par] = 0.0

        # store xb value
        self.xb = xb

    # wrapper function to get attribute
    def get_val(self,
                varname: str) -> float:
        # if xb is requested, return it
        if varname == "xb":
            return self.xb
        # otherwise return value from par_vals
        else:
            return self.par_vals[varname]

    # get difference between two values of varname
    def diff(self,
             other: 'Point',
             par_name: str) -> float:
        return self.get_val(par_name) - other.get_val(par_name)

    # get fractional difference between two values of varname
    # TODO: Add divide-by-zero protection
    def diff_frac(self,
                  other: 'Point',
                  par_name: str) -> float:
        return self.diff(other,par_name) / abs(self.get_val(par_name))
    
    # get formatted string of xb
    def format_xb(self) -> str:
        return f"{self.xb:.2E}"
    
    # get formatted string of parameter
    def format_param(self,
                     par_name: str) -> str:
        return "value = " + f"{self.get_val(par_name):1.{self.model.parameter(par_name)['precision']}f}"
    
    # get formatted string of parameter diff w.r.t. another point
    def format_diff(self,
                    other: 'Point',
                    par_name: str) -> str:
        return "diff. = " + f"{self.diff(other,par_name):1.{self.model.parameter(par_name)['precision']}f}"
    
    # get formatted string of parameter fractional diff w.r.t. another point
    def format_diff_frac(self,
                         other: 'Point',
                         par_name: str) -> str:
        return "rel. diff. = " + f"{self.diff_frac(other,par_name):1.2f}"

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
        return Point(self.model.name(), self.par_vals, self.xb*scale_factor)
    
    def __str__(self) -> str:
        return f"{self.xb}\n{self.par_vals}"
    
    def __repr__(self) -> str:
        return f"{self.xb}\n{self.par_vals}"
