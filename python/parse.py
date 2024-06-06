
# import numpy library as np
import numpy as np

# import list of arrays
import arrays

# import dip test for unimodality
import diptest

# import math for useful functions
import math

# import masses class to handle mass orderings
from masses import Masses

# import model class to initialize Point class
from model import Model

# import decimal class for nicely formatted strings
from decimal import Decimal

# class to parse arrays and provide details about data
class Parse:

    # load new set of arrays
    def __init__(self,
                 masses: Masses,
                 decay,
                 modelname,
                 filename = ""):
        
        # initialize model name
        self.modelname = modelname

        # initialize model
        self.model = Model(modelname)

        # initialize HName and SName
        self.HName = masses.HName
        self.SName = masses.SName

        # initialize decay mode
        self.decay = decay

        # get arrays if filename is provided
        if filename:
            self.readFile(filename)

    # load new arrays
    def readFile(self,filename):

        # create arrays object if it does not exist
        if not hasattr(self,"arr"):
            self.arr = arrays.Arrays(filename)

        # load arrays from new file if arrays object already exists
        else:
            self.arr.loadArrays(filename)

        # get arrays masked by filters
        self.getFilteredArrays()

    # get the arrays
    def getArrays(self):
        return self.arr

    # get arrays of the filters
    def getFilters(self):
        self.filters = np.multiply(self.arr.data['filt_width'],self.arr.data['filt_bounds'])

    # find the point that maximizes xb
    def getMaxPoint(self):

        # get index of maximum xsec times BR
        maxidx = np.argmax(self.xb)

        # get max xsec times BR
        maxxb = self.xb[maxidx]
        
        # make dictionary for parameter values for maxxb
        self.maxDict = {}

        # loop over parameter arrays
        for par, array in self.parArrays.items():
            self.maxDict[par] = array[maxidx]

        # return a point object holding xb and other parameters
        return Point(xb=maxxb,
                     modelname=self.modelname,
                     parvals=self.maxDict)

    # get the maximum xb
    def getXB(self,decay=""):

        # if no decay mode is provided, use stored decay mode
        if not decay:
            decay = self.decay

        # get production cross section
        xb_prod = self.getXBProd()

        # get branching ratio
        xb_decay = self.getXBDecay(decay)

        # get total xsec times BR
        xb = np.multiply(xb_prod,xb_decay)

        # return total xsec time BR
        return xb

    # get maximum xb for the production
    def getXBProd(self):

        # TODO: take decay as argument for other production modes

        # get production cross section
        xb_prod = np.multiply(self.x_X_gg,self.b_X_SH)

        return xb_prod

    # get maximum xb for the decay
    def getXBDecay(self,decay=""):

        # if no decay mode is provided, use stored decay mode
        if not decay:
            decay = self.decay

        # get appropriate BR for decay mode
        match decay:

            # 4b case
            case "SHbbbb":
                xb_decay = np.multiply(self.b_S_bb,self.b_H_bb)

            # bbtautau cases
            case "SbbHtautau":
                xb_decay = np.multiply(self.b_S_bb,self.b_H_tautau)
            case "StautauHbb":
                xb_decay = np.multiply(self.b_S_tautau,self.b_H_bb)
            case "SHbbtautau":
                arr1 = np.multiply(self.b_S_bb,self.b_H_tautau)
                arr2 = np.multiply(self.b_S_tautau,self.b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # bbWW cases
            case "SbbHWW":
                xb_decay = np.multiply(self.b_S_bb,self.b_H_WW)
            case "SWWHbb":
                xb_decay = np.multiply(self.b_S_WW,self.b_H_bb)
            case "SHbbWW":
                arr1 = np.multiply(self.b_S_bb,self.b_H_WW)
                arr2 = np.multiply(self.b_S_WW,self.b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # bbZZ cases
            case "SbbHZZ":
                xb_decay = np.multiply(self.b_S_bb,self.b_H_ZZ)
            case "SZZHbb":
                xb_decay = np.multiply(self.b_S_ZZ,self.b_H_bb)
            case "SHbbZZ":
                arr1 = np.multiply(self.b_S_bb,self.b_H_ZZ)
                arr2 = np.multiply(self.b_S_ZZ,self.b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "SVVHbb":
                xb_decay = np.multiply(np.add(self.b_S_WW,self.b_S_ZZ),self.b_H_bb)
            case "SbbHVV":
                xb_decay = np.multiply(self.b_S_bb,np.add(self.b_H_WW,self.b_H_ZZ))
            case "SHVVbb":
                arr1 = np.multiply(np.add(self.b_S_WW,self.b_S_ZZ),self.b_H_bb)
                arr2 = np.multiply(self.b_S_bb,np.add(self.b_H_WW,self.b_H_ZZ))
                xb_decay = np.add(arr1,arr2)

            # WWtautau cases
            case "SWWHtautau":
                xb_decay = np.multiply(self.b_S_WW,self.b_H_tautau)
            case "StautauHWW":
                xb_decay = np.multiply(self.b_S_tautau,self.b_H_WW)
            case "SHWWtautau":
                arr1 = np.multiply(self.b_S_WW,self.b_H_tautau)
                arr2 = np.multiply(self.b_S_tautau,self.b_H_WW)
                xb_decay = np.add(arr1,arr2)

            # ZZtautau cases
            case "SZZHtautau":
                xb_decay = np.multiply(self.b_S_ZZ,self.b_H_tautau)
            case "StautauHZZ":
                xb_decay = np.multiply(self.b_S_tautau,self.b_H_ZZ)
            case "SHZZtautau":
                arr1 = np.multiply(self.b_S_ZZ,self.b_H_tautau)
                arr2 = np.multiply(self.b_S_tautau,self.b_H_ZZ)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "SVVHtautau":
                xb_decay = np.multiply(np.add(self.b_S_WW,self.b_S_ZZ),self.b_H_tautau)
            case "StautauHVV":
                xb_decay = np.multiply(self.b_S_tautau,np.add(self.b_H_WW,self.b_H_ZZ))
            case "SHVVtautau":
                arr1 = np.multiply(np.add(self.b_S_WW,self.b_S_ZZ),self.b_H_tautau)
                arr2 = np.multiply(self.b_S_tautau,np.add(self.b_H_WW,self.b_H_ZZ))
                xb_decay = np.add(arr1,arr2)

            # bbgamgam cases
            case "SbbHgamgam":
                xb_decay = np.multiply(self.b_S_bb,self.b_H_gamgam)
            case "SgamgamHbb":
                xb_decay = np.multiply(self.b_S_gamgam,self.b_H_bb)
            case "SHbbgamgam":
                arr1 = np.multiply(self.b_S_bb,self.b_H_gamgam)
                arr2 = np.multiply(self.b_S_gamgam,self.b_H_bb)
                xb_decay = np.add(arr1,arr2)

            # all other cases
            case _:
                print("Unrecognized decay",decay)
                print("This should not have happened")
                quit()

        # return the decay BR
        return xb_decay

    # get minimum value of a parameter
    def getMin(self,varname):
        return np.min(self.parArrays[varname])

    # get maximum value of a parameter
    def getMax(self,varname):
        return np.max(self.parArrays[varname])
    
    # get arrays of all parameter as a dictionary
    def getParameters(self):
        return self.parArrays

    # apply filters as mask
    def getFilteredArrays(self):
        
        # get array of filters to use as a mask
        self.getFilters()

        ##############################
        # create local arrays by applying filter mask
        ##############################

        # dictionary for parameter arrays
        self.parArrays = {}

        # loop over parameters
        for name, par in self.model.params.items():
            # populate dictionary of parameter arrays
            self.parArrays[name] = self.arr.data[par['fullname']][self.filters != 0]

        # H1 xsec and BR values
        self.b_H_bb = self.arr.data['b_'+self.HName+'_bb'][self.filters != 0]
        self.b_H_tautau = self.arr.data['b_'+self.HName+'_tautau'][self.filters != 0]
        self.b_H_WW = self.arr.data['b_'+self.HName+'_WW'][self.filters != 0]
        self.b_H_ZZ = self.arr.data['b_'+self.HName+'_ZZ'][self.filters != 0]
        self.b_H_gamgam = self.arr.data['b_'+self.HName+'_gamgam'][self.filters != 0]

        # H2 xsec and BR values
        self.b_S_bb = self.arr.data['b_'+self.SName+'_bb'][self.filters != 0]
        self.b_S_tautau = self.arr.data['b_'+self.SName+'_tautau'][self.filters != 0]
        self.b_S_WW = self.arr.data['b_'+self.SName+'_WW'][self.filters != 0]
        self.b_S_ZZ = self.arr.data['b_'+self.SName+'_ZZ'][self.filters != 0]
        self.b_S_gamgam = self.arr.data['b_'+self.SName+'_gamgam'][self.filters != 0]

        # H3 xsec and BR values
        self.x_X_gg = self.arr.data['x_H3_gg'][self.filters != 0]
        self.b_X_SH = self.arr.data['b_H3_H1H2'][self.filters != 0]

        # cross-section times branching ratio
        self.xb = self.getXB()

    # function that checks whether xb is unimodal in a parameter
    def isBimodal(self,param_name):

        # percentile threshold for xb
        percentile_threshold = 98

        # number of points available
        npoints = len(self.xb)

        # minimum number of points for test
        min_points = 200

        # modify percentile threshold to ensure there are at least min_points
        if npoints * (1.0 - percentile_threshold / 100) < min_points:
            percentile_threshold = math.floor(100 * (1.0 - min_points/npoints))

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # get xb value that corresponds to percentile threshold
        threshold_value = np.percentile(self.xb, percentile_threshold)

        # get set of parameter values with xb in selected percentile
        param_selected = getattr(self,param_name)[self.xb > threshold_value]

        # use Hartigan's dip test for unimodality
        dip, pval = diptest.diptest(param_selected)

        # p-value threshold for multimodality
        pval_threshold = 0.05

        # if p-value is below threshold, return True, otherwise return False
        if pval < pval_threshold:
            return True
        else:
            return False

# class that holds parameter and xb values for a single point
class Point:

    # initialize point parameters
    def __init__(self,
                 modelname,
                 parvals=None,
                 xb=0):
        
        # get model
        self.model = Model(modelname)

        # if parvals exists, store it
        if parvals:
            self.parvals = parvals
        # otherwise create default dictionary from model
        else:
            # get list of parameters from model
            parlist = self.model.parameterList()

            # create empty dictionary
            self.parvals = {}
            # loop over list of parameters and make default dictionary
            for par in parlist:
                self.parvals[par] = 0

        # store xb value
        self.xb = xb

    # wrapper function to get attribute
    def getVal(self,varname):
        # if xb is requested, return it
        if varname == "xb":
            return self.xb
        # otherwise return value from parvals
        else:
            return self.parvals[varname]

    # get difference between two values of varname
    def diff(self, other: 'Point', parname):
        return self.getVal(parname) - other.getVal(parname)

    # get fractional difference between two values of varname
    # TODO: Add divide-by-zero protection
    def diffFrac(self, other: 'Point', parname):
        return self.diff(other,parname) / abs(self.getVal(parname))
    
    # get formatted string of xb
    def formatXB(self):
        return f"{Decimal(self.xb):.3E}"
    
    # get formatted string of parameter
    def formatParam(self, parname):
        return "value = " + f"{self.getVal(parname):1.{self.model.params[parname]['precision']}f}"
    
    # get formatted string of parameter diff w.r.t. another point
    def formatDiff(self, other: 'Point', parname):
        return "diff. = " + f"{self.diff(other,parname):1.{self.model.params[parname]['precision']}f}"
    
    # get formatted string of parameter fractional diff w.r.t. another point
    def formatDiffFrac(self, other: 'Point', parname):
        return "rel. diff. = " + f"{self.diffFrac(other,parname):1.2f}"

    # define the greater than (>) operator
    def __gt__(self,other: 'Point'):
        return self.xb > other.xb

    # define the less than (<) operator
    def __lt__(self,other: 'Point'):
        return self.xb < other.xb
