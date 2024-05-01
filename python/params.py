
import math

class Params:

    def __init__(self,mH,mS,mX):

        # make list of masses
        masses = [float(mH),float(mS),float(mX)]

        # sort masses in ascending order
        masses.sort()

        # set mass values
        self.mH1 = masses[0]
        self.mH2 = masses[1]
        self.mH3 = masses[2]

        # set min and max theta values
        # these should not be changed once initialized
        # TODO: make these configurable from arguments
        self.tHSmin = -1 * math.pi / 2
        self.tHSmax = math.pi / 2
        self.tHXmin = -1 * math.pi / 2
        self.tHXmax = math.pi / 2
        self.tSXmin = -1 * math.pi / 2
        self.tSXmax = math.pi / 2

        # set min and max vev values
        # these should not be changed once initialized
        # TODO: make these configurable from arguments
        self.vsmin = 0.0
        self.vsmax = 1000.0
        self.vxmin = 0.0
        self.vxmax = 1000.0

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
    def writeini(self,templateini,ininame):

        # read in template .ini file
        template = open(templateini,"r")
        filedata = template.read()
        template.close()

        # create filedata with parameters
        filedata = filedata.replace("MH1",str(self.mH1))
        filedata = filedata.replace("MH2",str(self.mH2))
        filedata = filedata.replace("MH3",str(self.mH3))
        filedata = filedata.replace("T1LOW",str(self.tHSlow))
        filedata = filedata.replace("T1HIGH",str(self.tHShigh))
        filedata = filedata.replace("T2LOW",str(self.tHXlow))
        filedata = filedata.replace("T2HIGH",str(self.tHXhigh))
        filedata = filedata.replace("T3LOW",str(self.tSXlow))
        filedata = filedata.replace("T3HIGH",str(self.tSXhigh))
        filedata = filedata.replace("VSLOW",str(self.vslow))
        filedata = filedata.replace("VSHIGH",str(self.vshigh))
        filedata = filedata.replace("VXLOW",str(self.vxlow))
        filedata = filedata.replace("VXHIGH",str(self.vxhigh))

        # write to .ini file
        outfile = open(ininame,"w")
        outfile.write(filedata)
        outfile.close()
