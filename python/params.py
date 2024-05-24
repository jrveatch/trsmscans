
import math

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

        # set min and max theta values
        self.tHSmin = self.model.min('tHS')
        self.tHSmax = self.model.max('tHS')
        self.tHXmin = self.model.min('tHX')
        self.tHXmax = self.model.max('tHX')
        self.tSXmin = self.model.min('tSX')
        self.tSXmax = self.model.max('tSX')

        # set min and max vev values
        self.vsmin = self.model.min('vs')
        self.vsmax = self.model.max('vs')
        self.vxmin = self.model.min('vx')
        self.vxmax = self.model.max('vx')

        # initialize high and low values from max and min values
        self.tHSlow = self.tHSmin
        self.tHShigh = self.tHSmax
        self.tHXlow = self.tHXmin
        self.tHXhigh = self.tHXmax
        self.tSXlow = self.tSXmin
        self.tSXhigh = self.tSXmax
        self.vslow = self.vsmin
        self.vshigh = self.vsmax
        self.vxlow = self.vxmin
        self.vxhigh = self.vxmax

        # initialize parameter values to midpoint of range
        self.tHSval = self.getMidPoint(low=self.tHSlow,high=self.tHShigh)
        self.tHXval = self.getMidPoint(low=self.tHXlow,high=self.tHXhigh)
        self.tSXval = self.getMidPoint(low=self.tSXlow,high=self.tSXhigh)
        self.vsval = self.getMidPoint(low=self.vslow,high=self.vshigh)
        self.vxval = self.getMidPoint(low=self.vxlow,high=self.vxhigh)

        # initialize parameter ranges
        self.tHSrange = self.getRange(low=self.tHSlow,high=self.tHShigh)
        self.tHXrange = self.getRange(low=self.tHXlow,high=self.tHXhigh)
        self.tSXrange = self.getRange(low=self.tSXlow,high=self.tSXhigh)
        self.vsrange = self.getRange(low=self.vslow,high=self.vshigh)
        self.vxrange = self.getRange(low=self.vxlow,high=self.vxhigh)

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # this also sets new range values

    def set_min(self,varname,val):
        setattr(self,varname+"min",val)
        if getattr(self,varname+"low") < getattr(self,varname+"min"):
            setattr(self,varname+"low",getattr(self,varname+"min"))
            setattr(self,varname+"range",self.getRange(low=getattr(self,varname+"low"),high=getattr(self,varname+"high")))

    def set_max(self,varname,val):
        setattr(self,varname+"max",val)
        if getattr(self,varname+"high") > getattr(self,varname+"max"):
            setattr(self,varname+"high",getattr(self,varname+"max"))
            setattr(self,varname+"range",self.getRange(low=getattr(self,varname+"low"),high=getattr(self,varname+"high")))

    # function to calculate parameter value
    def getMidPoint(self,low,high):
        return (low + high) / 2

    # function to calculate parameter ranges
    def getRange(self,low,high):
        return abs(high - low) / 2
    
    # function to get new low value
    def getNewLow(self,val,range,min):
        newLow = val - range
        if newLow < min:
            newLow = min
        return newLow
    
    # function to get new high value
    def getNewHigh(self,val,range,max):
        newHigh = val + range
        if newHigh > max:
            newHigh = max
        return newHigh

    # functions to set new low and high parameters
    # TODO: Give option to not pass in range and just use range that already exists
    # TODO: Use full range, not truncated range
    def set_params(self,varname,val,range):
        setattr(self,varname+"val",val)
        setattr(self,varname+"range",range)
        setattr(self,varname+"low",self.getNewLow(val,range,getattr(self,varname+"min")))
        setattr(self,varname+"high",self.getNewHigh(val,range,getattr(self,varname+"max")))

    # function to calculate volume
    def volume(self):
        volume = 1.0
        if abs(self.tHShigh - self.tHSlow) > 1e-13:
            volume *= abs(self.tHShigh - self.tHSlow)
        if abs(self.tHXhigh - self.tHXlow) > 1e-13:
            volume *= abs(self.tHXhigh - self.tHXlow)
        if abs(self.tSXhigh - self.tSXlow) > 1e-13:
            volume *= abs(self.tSXhigh - self.tSXlow)
        if abs(self.vshigh - self.vslow) > 1e-13:
            volume *= abs(self.vshigh - self.vslow)
        if abs(self.vxhigh - self.vxlow) > 1e-13:
            volume *= abs(self.vxhigh - self.vxlow)
        return volume

    # function to get min value
    def min(self,varname):
        return getattr(self,varname+"min")

    # function to get max value
    def max(self,varname):
        return getattr(self,varname+"max")

    # function to get low value
    def low(self,varname):
        return getattr(self,varname+"low")

    # function to get high value
    def high(self,varname):
        return getattr(self,varname+"high")
    
    # function to get parameter values
    def val(self,varname):
        return getattr(self,varname+"val")
    
    # function to get parameter ranges
    def range(self,varname):
        return getattr(self,varname+"range")
    
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
        # TODO: These probably need to be ordered by mass
        filedata = filedata.replace("tHS_LOW",str(self.tHSlow))
        filedata = filedata.replace("tHS_HIGH",str(self.tHShigh))
        filedata = filedata.replace("tHX_LOW",str(self.tHXlow))
        filedata = filedata.replace("tHX_HIGH",str(self.tHXhigh))
        filedata = filedata.replace("tSX_LOW",str(self.tSXlow))
        filedata = filedata.replace("tSX_HIGH",str(self.tSXhigh))
        filedata = filedata.replace("vs_LOW",str(self.vslow))
        filedata = filedata.replace("vs_HIGH",str(self.vshigh))
        filedata = filedata.replace("vx_LOW",str(self.vxlow))
        filedata = filedata.replace("vx_HIGH",str(self.vxhigh))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(filedata)
        outfile.close()
