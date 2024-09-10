
# import numpy library as np
import numpy as np
from numpy.typing import NDArray

# import list of arrays
from utils.arrays import Arrays

# import point
from utils.point import Point

# import dip test for unimodality
import diptest

# import math for useful functions
import math

# import masses class to handle mass orderings
from utils.masses import Masses

# import model class to initialize Point class
from utils.model import Model

# class to parse arrays and provide details about data
class Parse:

    # load new set of arrays
    def __init__(self,
                 masses: Masses,
                 model_name: str,
                 file_name: str = ""):
        
        # initialize model name
        self.__model_name = model_name

        # initialize model
        self.__model = Model(model_name)

        # initialize HName and SName
        self.__HName = masses.HName
        self.__SName = masses.SName

        # initialize x-sec, BR and indices arrays
        self.__b_H_bb: NDArray = None
        self.__b_H_tautau: NDArray = None
        self.__b_H_WW: NDArray = None
        self.__b_H_ZZ: NDArray = None
        self.__b_H_gamgam: NDArray = None
        self.__b_S_bb: NDArray = None
        self.__b_S_tautau: NDArray = None
        self.__b_S_WW: NDArray = None
        self.__b_S_ZZ: NDArray = None
        self.__b_S_gamgam: NDArray = None
        self.__x_X_gg: NDArray = None
        self.__b_X_SH: NDArray = None
        self.__prefilter_idx: NDArray = None

        # initialize dictionary of parameter arrays
        self.__par_arrays: dict[str,NDArray] = {}

        # initialize file data
        self.__file_content: list[str] = []

        # initialize max_xb line from .tsv file
        self.__max_xb_line: str = ""

        # get arrays from file name if it is provided
        if file_name:
            self.read_file(file_name)

    # load new arrays
    def read_file(self,
                  file_name: str) -> None:

        # create arrays object if it does not exist
        if not hasattr(self,"arrays"):
            self.arrays = Arrays(file_name)

        # load arrays from new file if arrays object already exists
        else:
            self.arrays.load_arrays(file_name)

        # read and store raw file content
        file = open(file_name)
        self.__file_content = file.readlines()

        # get arrays masked by filters
        self.__make_filtered_arrays()

        # reset max_xb line to make errors obvious
        self.__max_xb_line: str = ""

    # find the point that maximizes xb
    def get_max_xb_point(self,
                         decay: str) -> 'Point':
        
        # get xb
        xb = self.get_xb(decay)

        # get index of maximum xsec times BR
        maxidx = np.argmax(xb)

        # get max xsec times BR
        maxxb = xb[maxidx]

        # get prefilter index of max xb point
        prefilter_idx = self.__prefilter_idx[maxidx]

        # store max xb line - add 1 to account for header
        self.__max_xb_line = self.__file_content[prefilter_idx+1]
        
        # make dictionary for parameter values for maxxb
        maxxb_parvals: dict[str,float] = {}

        # loop over parameter arrays and store optimal value of each
        for par, array in self.__par_arrays.items():
            maxxb_parvals[par] = array[maxidx]

        # return a point object holding xb and other parameters
        return Point(xb = maxxb,
                     model_name = self.__model_name,
                     parvals = maxxb_parvals)

    # get line from .tsv corresponding to max xb point
    def get_max_xb_line(self) -> str:
        return self.__max_xb_line

    # get minimum value of a parameter
    def get_min(self,
                parname: str) -> float:
        return np.min(self.__par_arrays[parname])

    # get maximum value of a parameter
    def get_max(self,
                parname: str) -> float:
        return np.max(self.__par_arrays[parname])
    
    # get arrays of all parameter as a dictionary
    def get_parameter_arrays(self) -> dict[str,NDArray]:
        return self.__par_arrays

    # function that checks whether xb is unimodal in a parameter
    def is_bimodal(self,
                   param_name: str,
                   decay: str) -> bool:

        # percentile threshold for xb
        percentile_threshold = 98

        # get xb
        xb = self.get_xb(decay)

        # number of points available
        npoints = len(xb)

        # minimum number of points for test
        min_points = 200

        # modify percentile threshold to ensure there are at least min_points
        if npoints * (1.0 - percentile_threshold / 100) < min_points:
            percentile_threshold = math.floor(100 * (1.0 - min_points/npoints))

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # get xb value that corresponds to percentile threshold
        threshold_value = np.percentile(xb, percentile_threshold)

        # get set of parameter values with xb in selected percentile
        param_selected = self.__par_arrays[param_name][xb > threshold_value] 

        # use Hartigan's dip test for unimodality
        dip, pval = diptest.diptest(param_selected)

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        if pval < pval_threshold:
            return True
        else:
            return False

    # get xb array
    def get_xb(self,
               decay: str) -> NDArray:

        # get production cross section
        xb_prod = self.__get_xb_prod()

        # get branching ratio
        xb_decay = self.__get_xb_decay(decay)

        # get total xsec times BR
        xb = np.multiply(xb_prod,xb_decay)

        # return total xsec time BR
        return xb

    # get maximum xb for the production
    def __get_xb_prod(self) -> NDArray:

        # TODO: take decay as argument for other production modes

        # get production cross section
        xb_prod = np.multiply(self.__x_X_gg,self.__b_X_SH)

        return xb_prod

    # get maximum xb for the decay
    def __get_xb_decay(self,
                       decay: str) -> NDArray:

        # get appropriate BR for decay mode
        match decay:

            # 4b case
            case "SHbbbb":
                xb_decay = np.multiply(self.__b_S_bb,self.__b_H_bb)

            # bbtautau cases
            case "SbbHtautau":
                xb_decay = np.multiply(self.__b_S_bb,self.__b_H_tautau)
            case "StautauHbb":
                xb_decay = np.multiply(self.__b_S_tautau,self.__b_H_bb)
            case "SHbbtautau":
                arr1 = np.multiply(self.__b_S_bb,self.__b_H_tautau)
                arr2 = np.multiply(self.__b_S_tautau,self.__b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # bbWW cases
            case "SbbHWW":
                xb_decay = np.multiply(self.__b_S_bb,self.__b_H_WW)
            case "SWWHbb":
                xb_decay = np.multiply(self.__b_S_WW,self.__b_H_bb)
            case "SHbbWW":
                arr1 = np.multiply(self.__b_S_bb,self.__b_H_WW)
                arr2 = np.multiply(self.__b_S_WW,self.__b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # bbZZ cases
            case "SbbHZZ":
                xb_decay = np.multiply(self.__b_S_bb,self.__b_H_ZZ)
            case "SZZHbb":
                xb_decay = np.multiply(self.__b_S_ZZ,self.__b_H_bb)
            case "SHbbZZ":
                arr1 = np.multiply(self.__b_S_bb,self.__b_H_ZZ)
                arr2 = np.multiply(self.__b_S_ZZ,self.__b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "SVVHbb":
                xb_decay = np.multiply(np.add(self.__b_S_WW,self.__b_S_ZZ),self.__b_H_bb)
            case "SbbHVV":
                xb_decay = np.multiply(self.__b_S_bb,np.add(self.__b_H_WW,self.__b_H_ZZ))
            case "SHVVbb":
                arr1 = np.multiply(np.add(self.__b_S_WW,self.__b_S_ZZ),self.__b_H_bb)
                arr2 = np.multiply(self.__b_S_bb,np.add(self.__b_H_WW,self.__b_H_ZZ))
                xb_decay = np.add(arr1,arr2)

            # WWtautau cases
            case "SWWHtautau":
                xb_decay = np.multiply(self.__b_S_WW,self.__b_H_tautau)
            case "StautauHWW":
                xb_decay = np.multiply(self.__b_S_tautau,self.__b_H_WW)
            case "SHWWtautau":
                arr1 = np.multiply(self.__b_S_WW,self.__b_H_tautau)
                arr2 = np.multiply(self.__b_S_tautau,self.__b_H_WW)
                xb_decay = np.add(arr1,arr2)

            # ZZtautau cases
            case "SZZHtautau":
                xb_decay = np.multiply(self.__b_S_ZZ,self.__b_H_tautau)
            case "StautauHZZ":
                xb_decay = np.multiply(self.__b_S_tautau,self.__b_H_ZZ)
            case "SHZZtautau":
                arr1 = np.multiply(self.__b_S_ZZ,self.__b_H_tautau)
                arr2 = np.multiply(self.__b_S_tautau,self.__b_H_ZZ)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "SVVHtautau":
                xb_decay = np.multiply(np.add(self.__b_S_WW,self.__b_S_ZZ),self.__b_H_tautau)
            case "StautauHVV":
                xb_decay = np.multiply(self.__b_S_tautau,np.add(self.__b_H_WW,self.__b_H_ZZ))
            case "SHVVtautau":
                arr1 = np.multiply(np.add(self.__b_S_WW,self.__b_S_ZZ),self.__b_H_tautau)
                arr2 = np.multiply(self.__b_S_tautau,np.add(self.__b_H_WW,self.__b_H_ZZ))
                xb_decay = np.add(arr1,arr2)

            # bbgamgam cases
            case "SbbHgamgam":
                xb_decay = np.multiply(self.__b_S_bb,self.__b_H_gamgam)
            case "SgamgamHbb":
                xb_decay = np.multiply(self.__b_S_gamgam,self.__b_H_bb)
            case "SHbbgamgam":
                arr1 = np.multiply(self.__b_S_bb,self.__b_H_gamgam)
                arr2 = np.multiply(self.__b_S_gamgam,self.__b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # all other cases
            case _:
                print("Unrecognized decay",decay)
                print("This should not have happened")
                quit()

        # return the decay BR
        return xb_decay

    # get arrays of the filters
    def __set_filters(self) -> None:
        self.__filters = self.arrays.data('filt_width') * self.arrays.data('filt_bounds') * self.arrays.data('filt_signals')

    # apply filters as mask
    def __make_filtered_arrays(self) -> None:
        
        # get array of filters to use as a mask
        self.__set_filters()

        ##############################
        # create local arrays by applying filter mask
        ##############################

        # loop over parameters
        for name, par in self.__model.parameters().items():
            # populate dictionary of parameter arrays
            self.__par_arrays[name] = self.arrays.data(par['fullname'])[self.__filters != 0]

        # H xsec and BR values
        self.__b_H_bb = self.arrays.data('b_'+self.__HName+'_bb')[self.__filters != 0]
        self.__b_H_tautau = self.arrays.data('b_'+self.__HName+'_tautau')[self.__filters != 0]
        self.__b_H_WW = self.arrays.data('b_'+self.__HName+'_WW')[self.__filters != 0]
        self.__b_H_ZZ = self.arrays.data('b_'+self.__HName+'_ZZ')[self.__filters != 0]
        self.__b_H_gamgam = self.arrays.data('b_'+self.__HName+'_gamgam')[self.__filters != 0]

        # S xsec and BR values
        self.__b_S_bb = self.arrays.data('b_'+self.__SName+'_bb')[self.__filters != 0]
        self.__b_S_tautau = self.arrays.data('b_'+self.__SName+'_tautau')[self.__filters != 0]
        self.__b_S_WW = self.arrays.data('b_'+self.__SName+'_WW')[self.__filters != 0]
        self.__b_S_ZZ = self.arrays.data('b_'+self.__SName+'_ZZ')[self.__filters != 0]
        self.__b_S_gamgam = self.arrays.data('b_'+self.__SName+'_gamgam')[self.__filters != 0]

        # X xsec and BR values
        self.__x_X_gg = self.arrays.data('x_H3_gg')[self.__filters != 0]
        self.__b_X_SH = self.arrays.data('b_H3_H1H2')[self.__filters != 0]

        # original indices
        self.__prefilter_idx = self.arrays.data('idx')[self.__filters != 0]

    # get number of filtered events
    def get_n_points(self) -> int:
        return next(iter(self.__par_arrays.values())).size

    # get number of unfiltered events
    def get_n_unfiltered_points(self) -> int:
        return self.arrays.data().shape[0]
