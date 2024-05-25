
from masses import Masses
from model import Model
from parse import Point

# class to hold and update full set of parameters used in a scan
class Params:

    def __init__(self,
                 modelname,
                 masses: Masses):

        # store masses
        self.masses = masses

        # set H1/2/3 mass values
        self.mH1 = masses.mH1
        self.mH2 = masses.mH2
        self.mH3 = masses.mH3

        # get model using modelname
        self.model = Model(modelname)

        # get list of parameter names
        self.parnames = self.model.parameterList()

        # create dictionary of parameters
        self.parameters = {}
        for key in self.parnames:
            self.parameters[key] = Parameter(key,self.model.params[key])

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # these also set new range values

    def setMin(self,parname,newMin):
        self.parameters[parname].setMin(newMin)

    def setMax(self,parname,newMax):
        self.parameters[parname].setMax(newMax)

    # function to calculate parameter value
    def getMidPoint(self,low,high):
        return (low + high) / 2

    # function to calculate parameter ranges
    def getRange(self,low,high):
        return abs(high - low) / 2

    # set new value, range, low and high
    def updateParams(self,
                     newPoint: 'Point'=None,
                     rangeScale=1.0):

        # if both newPoint is None and rangeScale is 1.0, complain and return existing low
        if newPoint is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        # loop over parameters
        for parname in self.parnames:

            # initialize new value to be None
            newVal = None

            # if new point is provided, get new value from it
            if newPoint:
                newVal = newPoint.getVal(parname)

            # update parameter with new value and range scale
            self.parameters[parname].updateParam(newVal=newVal,
                                                 rangeScale=rangeScale)

    # function to calculate volume of parameter space
    def volume(self):

        # initialize volume to 1
        volume = 1.0

        # loop over parameters
        for par in self.parameters.values():
        
            # make sure range is non-zero
            if par.range > 1e-13:
        
                # multiply volume by parameter range
                volume *= par.range
        
        return volume

    # function to get min value
    def min(self,parname):
        return self.parameters[parname].min

    # function to get max value
    def max(self,parname):
        return self.parameters[parname].max

    # function to get low value
    def low(self,parname):
        return self.parameters[parname].low

    # function to get high value
    def high(self,parname):
        return self.parameters[parname].high
    
    # function to get parameter values
    def val(self,parname):
        return self.parameters[parname].val
    
    # function to get parameter ranges
    def range(self,parname):
        return self.parameters[parname].range
    
    # function to write .ini file with parameters
    def writeini(self,ininame):

        # read in template .ini file
        template = open(self.model.templateini,"r")
        filedata = template.read()
        template.close()

        # create filedata with parameters
        filedata = filedata.replace("MH1",str(self.mH1))
        filedata = filedata.replace("MH2",str(self.mH2))
        filedata = filedata.replace("MH3",str(self.mH3))
        # loop over parameters and fill low/high values
        for par in self.parameters.values():
            filedata = filedata.replace(par.name+"_LOW",str(par.low))
            filedata = filedata.replace(par.name+"_HIGH",str(par.high))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(filedata)
        outfile.close()

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,name,dict):

        # initialize parameter name
        self.name = name

        # initialize values from dictionary
        self.fullname = dict['fullname']
        self.precision = dict['precision']
        self.min = dict['min']
        self.max = dict['max']

        # initialize low and high from min and max
        self.low = self.min
        self.high = self.max

        # initialize value as the midpoint
        self.val = self.getMidPoint()

        # initialize range
        self.range = self.getRange()

    # get the midpoint given current low and high
    def getMidPoint(self):
        return (self.low + self.high) / 2

    # get range given current low and high
    def getRange(self):
        return abs(self.high - self.low)

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # this also sets new range values

    def setMin(self,newMin):
        self.min = newMin
        if self.low < self.min:
            self.low = self.min
            self.range = self.getRange()

    def setMax(self,newMax):
        self.max = newMax
        if self.high > self.max:
            self.high = self.max
            self.range = self.getRange()
    
    # set new value, range, low and high
    def updateParam(self,newVal=None,rangeScale=1.0):

        # if both newVal is None and rangeScale is 1.0, complain and return existing low
        if newVal is None and rangeScale == 1.0:
            print("Attempting to update parameter with no new information... returning...")
            return

        # if a new val is given, update stored val
        if newVal:
            self.val = newVal

        # scale range by given value
        self.range *= rangeScale

        # find new low and high using the half range
        self.low = self.val - self.range / 2
        self.high = self.val + self.range / 2

        # adjust low and high based on min
        if self.low < self.min:
            
            # calculate how much the new low is below min
            overage = self.min - self.low

            # add overage to high
            self.high += overage

            # if new high is above max, set it to max
            if self.high > self.max:
                self.high = self.max

            # set low to min
            self.low = self.min

        # adjust high and low based on max
        if self.high > self.max:

            # calculate how much the new high is above max
            overage = self.high - self.max

            # subtract overage from low
            self.low -= overage

            # if new low is below min, set it to min
            if self.low < self.min:
                self.low = self.min
            
            # set high to max
            self.high = self.max

        return
