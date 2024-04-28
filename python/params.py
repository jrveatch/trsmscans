
import math

class Params:

    def __init__(self,mH,mS,mX):

        # make list of masses
        masses = [float(mH),float(mS),float(mX)]

        # sort masses in ascending order
        masses.sort()

        # set mass values
        self._mH1 = masses[0]
        self._mH2 = masses[1]
        self._mH3 = masses[2]

        # set min and max theta values
        # these should not be changed once initialized
        # TODO: make these configurable from arguments
        self._tHSmin = -1 * math.pi / 2
        self._tHSmax = math.pi / 2
        self._tHXmin = -1 * math.pi / 2
        self._tHXmax = math.pi / 2
        self._tSXmin = -1 * math.pi / 2
        self._tSXmax = math.pi / 2

        # set min and max vev values
        # these should not be changed once initialized
        # TODO: make these configurable from arguments
        self._vsmin = 0.0
        self._vsmax = 1000.0
        self._vxmin = 0.0
        self._vxmax = 1000.0

        # initialize high and low values from max and min values
        self._tHSlow = self._tHSmin
        self._tHShigh = self._tHSmax
        self._tHXlow = self._tHXmin
        self._tHXhigh = self._tHXmax
        self._tSXlow = self._tSXmin
        self._tSXhigh = self._tSXmax
        self._vslow = self._vsmin
        self._vshigh = self._vsmax
        self._vxlow = self._vxmin
        self._vxhigh = self._vxmax

        # initialize parameter values to midpoint of range
        self._tHSval = self.getMidPoint(low=self._tHSlow,high=self._tHShigh)
        self._tHXval = self.getMidPoint(low=self._tHXlow,high=self._tHXhigh)
        self._tSXval = self.getMidPoint(low=self._tSXlow,high=self._tSXhigh)
        self._vsval = self.getMidPoint(low=self._vslow,high=self._vshigh)
        self._vxval = self.getMidPoint(low=self._vxlow,high=self._vxhigh)

        # initialize parameter ranges
        self._tHSrange = self.getRange(low=self._tHSlow,high=self._tHShigh)
        self._tHXrange = self.getRange(low=self._tHXlow,high=self._tHXhigh)
        self._tSXrange = self.getRange(low=self._tSXlow,high=self._tSXhigh)
        self._vsrange = self.getRange(low=self._vslow,high=self._vshigh)
        self._vxrange = self.getRange(low=self._vxlow,high=self._vxhigh)

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them
    # this also sets new range values

    def set_min(self,varname,val):
        setattr(self,"_"+varname+"min",val)
        if getattr(self,"_"+varname+"low") < getattr(self,"_"+varname+"min"):
            setattr(self,"_"+varname+"low",getattr(self,"_"+varname+"min"))
            setattr(self,"_"+varname+"range",self.getRange(low=getattr(self,"_"+varname+"low"),high=getattr(self,"_"+varname+"high")))

    def set_max(self,varname,val):
        setattr(self,"_"+varname+"max",val)
        if getattr(self,"_"+varname+"high") > getattr(self,"_"+varname+"max"):
            setattr(self,"_"+varname+"high",getattr(self,"_"+varname+"max"))
            setattr(self,"_"+varname+"range",self.getRange(low=getattr(self,"_"+varname+"low"),high=getattr(self,"_"+varname+"high")))

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
        setattr(self,"_"+varname+"val",val)
        setattr(self,"_"+varname+"range",range)
        setattr(self,"_"+varname+"low",self.getNewLow(val,range,getattr(self,"_"+varname+"min")))
        setattr(self,"_"+varname+"high",self.getNewHigh(val,range,getattr(self,"_"+varname+"max")))

    # function to calculate volume
    def volume(self):
        volume = 1.0
        if abs(self._tHShigh - self._tHSlow) > 1e-13:
            volume *= abs(self._tHShigh - self._tHSlow)
        if abs(self._tHXhigh - self._tHXlow) > 1e-13:
            volume *= abs(self._tHXhigh - self._tHXlow)
        if abs(self._tSXhigh - self._tSXlow) > 1e-13:
            volume *= abs(self._tSXhigh - self._tSXlow)
        if abs(self._vshigh - self._vslow) > 1e-13:
            volume *= abs(self._vshigh - self._vslow)
        if abs(self._vxhigh - self._vxlow) > 1e-13:
            volume *= abs(self._vxhigh - self._vxlow)
        return volume

    # functions to get min and max values

    def min(self,varname):
        return getattr(self,"_"+varname+"min")

    def max(self,varname):
        return getattr(self,"_"+varname+"max")
    
    # functions to get low and high values

    def low(self,varname):
        return getattr(self,"_"+varname+"low")

    def high(self,varname):
        return getattr(self,"_"+varname+"high")
    
    # functions to get parameter values

    def val(self,varname):
        return getattr(self,"_"+varname+"val")
    
    # functions to get parameter ranges

    def range(self,varname):
        return getattr(self,"_"+varname+"range")
    
    # function to write .ini file with parameters
    def writeini(self,templateini,ininame):

        # read in template .ini file
        template = open(templateini,"r")
        filedata = template.read()
        template.close()

        filedata = filedata.replace("MH1",str(self._mH1))
        filedata = filedata.replace("MH2",str(self._mH2))
        filedata = filedata.replace("MH3",str(self._mH3))
        filedata = filedata.replace("T1LOW",str(self._tHSlow))
        filedata = filedata.replace("T1HIGH",str(self._tHShigh))
        filedata = filedata.replace("T2LOW",str(self._tHXlow))
        filedata = filedata.replace("T2HIGH",str(self._tHXhigh))
        filedata = filedata.replace("T3LOW",str(self._tSXlow))
        filedata = filedata.replace("T3HIGH",str(self._tSXhigh))
        filedata = filedata.replace("VSLOW",str(self._vslow))
        filedata = filedata.replace("VSHIGH",str(self._vshigh))
        filedata = filedata.replace("VXLOW",str(self._vxlow))
        filedata = filedata.replace("VXHIGH",str(self._vxhigh))

        outfile = open(ininame,"w")
        outfile.write(filedata)
        outfile.close()
