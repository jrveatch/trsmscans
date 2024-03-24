
import math

class Params:

    def __init__(self,mH1,mH2,mH3):

        # set mass values
        self._mH1 = mH1
        self._mH2 = mH2
        self._mH3 = mH3

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

        # initialize mean values
        self._tHSmean = self.getMean(self._tHSlow,self._tHShigh)
        self._tHXmean = self.getMean(self._tHXlow,self._tHXhigh)
        self._tSXmean = self.getMean(self._tSXlow,self._tSXhigh)
        self._vsmean = self.getMean(self._vslow,self._vshigh)
        self._vxmean = self.getMean(self._vxlow,self._vxhigh)

        # initialize parameter ranges
        self._tHSrange = self.getRange(self._tHSlow,self._tHShigh)
        self._tHXrange = self.getRange(self._tHXlow,self._tHXhigh)
        self._tSXrange = self.getRange(self._tSXlow,self._tSXhigh)
        self._vsrange = self.getRange(self._vslow,self._vshigh)
        self._vxrange = self.getRange(self._vxlow,self._vxhigh)

    # functions to set min and max values
    # if the current high or low values are beyond
    # the new min or max, set them

    def set_tHSmin(self,val):
        self._tHSmin = val
        if self._tHSlow < self._tHSmin:
            self._tHSlow = self._tHSmin

    def set_tHSmax(self,val):
        self._tHSmax = val
        if self._tHShigh > self._tHSmax:
            self._tHShigh = self._tHSmax

    def set_tHXmin(self,val):
        self._tHXmin = val
        if self._tHXlow < self._tHXmin:
            self._tHXlow = self._tHXmin

    def set_tHXmax(self,val):
        self._tHXmax = val
        if self._tHXhigh > self._tHXmax:
            self._tHXhigh = self._tHXmax

    def set_tSXmin(self,val):
        self._tSXmin = val
        if self._tSXlow < self._tSXmin:
            self._tSXlow = self._tSXmin

    def set_tSXmax(self,val):
        self._tSXmax = val
        if self._tSXhigh > self._tSXmax:
            self._tSXhigh = self._tSXmax

    def set_vsmin(self,val):
        self._vsmin = val
        if self._vslow < self._vsmin:
            self._vslow = self._vsmin

    def set_vsmax(self,val):
        self._vsmax = val
        if self._vshigh > self._vsmax:
            self._vshigh = self._vsmax

    def set_vxmin(self,val):
        self._vxmin = val
        if self._vxlow < self._vxmin:
            self._vxlow = self._vxmin

    def set_vxmax(self,val):
        self._vxmax = val
        if self._vxhigh > self._vxmax:
            self._vxhigh = self._vxmax

    # function to calculate mean parameter value
    
    def getMean(self,val1,val2):
        return (val1 + val2) / 2

    # function to calculate parameter ranges
    
    def getRange(self,val1,val2):
        return abs(val1 - val2) / 2
    
    # function to get new low value

    def getNewLow(self,mean,range,min):
        newLow = mean - range / 2
        if newLow < min:
            newLow = min
        return newLow
    
    # function to get new high value

    def getNewHigh(self,mean,range,max):
        newHigh = mean + range / 2
        if newHigh > max:
            newHigh = max
        return newHigh

    # functions to set new low and high parameters

    def set_tHSvals(self,mean,range):
        self._tHSmean = mean
        self._tHSrange = range
        self._tHSlow = self.getNewLow(mean,range,self._tHSmin)
        self._tHShigh = self.getNewHigh(mean,range,self._tHSmax)

    def set_tHXvals(self,mean,range):
        self._tHXmean = mean
        self._tHXrange = range
        self._tHXlow = self.getNewLow(mean,range,self._tHXmin)
        self._tHXhigh = self.getNewHigh(mean,range,self._tHXmax)

    def set_tSXvals(self,mean,range):
        self._tSXmean = mean
        self._tSXrange = range
        self._tSXlow = self.getNewLow(mean,range,self._tSXmin)
        self._tSXhigh = self.getNewHigh(mean,range,self._tSXmax)

    def set_vsvals(self,mean,range):
        self._vsmean = mean
        self._vsrange = range
        self._vslow = self.getNewLow(mean,range,self._vsmin)
        self._vshigh = self.getNewHigh(mean,range,self._vsmax)

    def set_vxvals(self,mean,range):
        self._vxmean = mean
        self._vxrange = range
        self._vxlow = self.getNewLow(mean,range,self._vxmin)
        self._vxhigh = self.getNewHigh(mean,range,self._vxmax)

    # function to calculate volume
    
    def volume(self):
        volume = abs(self._tHShigh - self._tHSlow)
        volume *= abs(self._tHXhigh - self._tHXlow)
        volume *= abs(self._tSXhigh - self._tSXlow)
        volume *= abs(self._vshigh - self._vslow)
        volume *= abs(self._vxhigh - self._vxlow)
        return volume

    # functions to get min and max values
        
    def tHSmin(self):
        return self._tHSmin
    
    def tHSmax(self):
        return self._tHSmax
    
    def tHXmin(self):
        return self._tHXmin
    
    def tHXmax(self):
        return self._tHXmax
    
    def tSXmin(self):
        return self._tSXmin
    
    def tSXmax(self):
        return self._tSXmax
    
    def vsmin(self):
        return self._vsmin
    
    def vsmax(self):
        return self._vsmax
    
    def vxmin(self):
        return self._vxmin
    
    def vxmax(self):
        return self._vxmax
    
    # functions to get low and high values
        
    def tHSlow(self):
        return self._tHSlow
    
    def tHShigh(self):
        return self._tHShigh
    
    def tHXlow(self):
        return self._tHXlow
    
    def tHXhigh(self):
        return self._tHXhigh
    
    def tSXlow(self):
        return self._tSXlow
    
    def tSXhigh(self):
        return self._tSXhigh
    
    def vslow(self):
        return self._vslow
    
    def vshigh(self):
        return self._vshigh
    
    def vxlow(self):
        return self._vxlow
    
    def vxhigh(self):
        return self._vxhigh
    
    # functions to get mean values
        
    def tHSmean(self):
        return self._tHSmean
    
    def tHXmean(self):
        return self._tHXmean
    
    def tSXmean(self):
        return self._tSXmean
    
    def vsmean(self):
        return self._vsmean
    
    def vxmean(self):
        return self._vxmean
    
    # functions to get parameter ranges
        
    def tHSrange(self):
        return self._tHSrange
    
    def tHXrange(self):
        return self._tHXrange
    
    def tSXrange(self):
        return self._tSXrange
    
    def vsrange(self):
        return self._vsrange
    
    def vxrange(self):
        return self._vxrange
    
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
