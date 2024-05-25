
from masses import Masses
from model import Model

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
    # TODO: Update this to use a point and range rate
    def updateParam(self,parname,newVal=None,newRange=None):
        self.parameters[parname].updateParam(newVal=newVal,newRange=newRange)

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
    # TODO: Remove the /2 to get full range instead of the half range
    def getRange(self):
        return abs(self.high - self.low) / 2

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
    # TODO: Update this to use a point and range rate
    def updateParam(self,newVal=None,newRange=None):

        # if both newVal and newRange are none, complain and return existing low
        if newVal is None and newRange is None:
            print("Attempting to set a new low with no new information... returning...")
            return

        # if a new val is given, update stored val
        if newVal:
            self.val = newVal

        # if a new range is given, update stored range
        if newRange:
            self.range = newRange

        # find new low and high
        # TODO: Fix this to use full range (divide it by 2)
        self.low = self.val - self.range
        self.high = self.val + self.range

        # adjust low based on min
        # TODO: Fix this to use full range - find overage and add it to the other side
        if self.low < self.min:
            self.low = self.min

        # adjust high based on max
        # TODO: Fix this to use full range - find overage and add it to the other side
        if self.high > self.max:
            self.high = self.max

        return
