
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
        self.__model = Model(modelname)

        # get list of parameter names
        self.parnames = self.__model.model_parameter_names()

        # create dictionary of parameters
        self.parameters = {}
        for par in self.parnames:
            self.parameters[par] = Parameter(par,self.__model.model_parameter(par))

    # get starting min value from model
    def starting_min(self,parname) -> float:
        return self.__model.starting_min(parname)

    # get starting max value from model
    def starting_max(self,parname) -> float:
        return self.__model.starting_max(parname)
    
    # get model name
    def model_name(self) -> str:
        return self.__model.model_name()

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # these also set new range values

    def setLowerBound(self,parname,newMin):
        self.parameters[parname].setLowerBound(newMin)

    def setUpperBound(self,parname,newMax):
        self.parameters[parname].setUpperBound(newMax)

    # set new value, range, low and high
    def scaleRanges(self,
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
            self.parameters[parname].scaleRange(newVal=newVal,
                                                 rangeScale=rangeScale)

    # update both low and high of each parameter using dictionaries
    def updateLowHigh(self, lowdict:dict=None, highdict:dict=None):

        # check to see if lowdict exists
        if lowdict is not None:

            # loop over parameters
            for parname, newlow in lowdict.items():
                if parname in self.parameters:
                    # use lowdict to update the low for each parameter
                    self.parameters[parname].updateLow(newlow)
                else:
                    print(f"Warning: {parname} is not known")
            
        # check to see if highdict exists
        if highdict is not None:

            # loop over parameters
            for parname, newhigh in highdict.items():
                if parname in self.parameters:
                    # use highdict to update the high for each parameter
                    self.parameters[parname].updateHigh(newhigh)
                else:
                    print(f"Warning: {parname} is not known")

    # function to calculate volume of parameter space
    def volume(self):

        # initialize volume to 1
        volume = 1.0

        # loop over parameters
        for par in self.parameters.values():
        
            # make sure range is non-zero
            if par.high - par.low > 1e-13:
        
                # multiply volume by parameter range
                volume *= par.high - par.low
        
        return volume

    # function to get min value
    def min(self,parname):
        return self.parameters[parname].lowerBound

    # function to get max value
    def max(self,parname):
        return self.parameters[parname].upperBound

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
        template = open(self.__model.template_ini(),"r")
        inidata = template.read()
        template.close()

        # create inidata with parameters
        inidata = inidata.replace("MH1",str(self.mH1))
        inidata = inidata.replace("MH2",str(self.mH2))
        inidata = inidata.replace("MH3",str(self.mH3))

        # loop over parameters and fill low/high values
        for par in self.parameters.values():
            inidata = inidata.replace(par.name+"_LOW",str(par.low))
            inidata = inidata.replace(par.name+"_HIGH",str(par.high))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(inidata)
        outfile.close()

    # print min and max for a parameter
    def printMinMax(self,parname):
        self.parameters[parname].printMinMax()

# class to hold and update a single model parameter
class Parameter:

    def __init__(self,name,dict):

        # initialize parameter name
        self.name = name

        # initialize values from dictionary
        self.fullname = dict['fullname']
        self.precision = dict['precision']
        self.lowerBound = dict['min']
        self.upperBound = dict['max']

        # initialize low and high from min and max
        self.low = self.lowerBound
        self.high = self.upperBound

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

    def setLowerBound(self,newMin):
        self.lowerBound = newMin
        if self.low < self.lowerBound:
            self.low = self.lowerBound
            self.range = self.getRange()

    def setUpperBound(self,newMax):
        self.upperBound = newMax
        if self.high > self.upperBound:
            self.high = self.upperBound
            self.range = self.getRange()
    
    # set new value, range, low and high
    def scaleRange(self,newVal=None,rangeScale=1.0):

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
        if self.low < self.lowerBound:
            
            # calculate how much the new low is below min
            overage = self.lowerBound - self.low

            # add overage to high
            self.high += overage

            # if new high is above max, set it to max
            if self.high > self.upperBound:
                self.high = self.upperBound

            # set low to min
            self.low = self.lowerBound

        # adjust high and low based on max
        if self.high > self.upperBound:

            # calculate how much the new high is above max
            overage = self.high - self.upperBound

            # subtract overage from low
            self.low -= overage

            # if new low is below min, set it to min
            if self.low < self.lowerBound:
                self.low = self.lowerBound
            
            # set high to max
            self.high = self.upperBound

        return
    
    # update the low to a new value
    def updateLow(self, newval):

        # check if newval is higher than previous low
        if newval < self.lowerBound:
            self.setLow(self.lowerBound)
            return

        # update low to our newval
        self.setLow(newval)
    
    # update the high to a new value
    def updateHigh(self, newval):

        # check if newval is lower than previous high
        if newval > self.upperBound:
            self.setHigh(self.upperBound)
            return

        # update high to our newval
        self.setHigh(newval)

    # set the new low and update the range to reflect the new low
    def setLow(self, newval):
        self.low = newval
        self.range = self.getRange()
    
    def setHigh(self, newval):
        self.high = newval
        self.range = self.getRange()
    
    # print min and max
    def printMinMax(self):
        print(self.name+": ["+f"{self.lowerBound:1.{self.precision}f}"+","+f"{self.upperBound:1.{self.precision}f}"+"]")

    # get formatted string showing range
    def formatRange(self):
        stringRange = "range = ["
        stringRange += f"{self.low:1.{self.precision}f}"
        stringRange += ","
        stringRange += f"{self.high:1.{self.precision}f}"
        stringRange += "]"
        return stringRange
