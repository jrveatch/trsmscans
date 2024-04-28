
# import numpy library as np
import numpy as np

# import list of arrays
import arrays

class Parse:

    # load new set of arrays
    def __init__(self,filename,HMass,SMass):

        # initialize HName and SName
        self.HName = ""
        self.SName = ""

        # assign H and S to H1 and H2
        if SMass > HMass:
            self.HName = "H1"
            self.SName = "H2"
        else:
            self.HName = "H2"
            self.SName = "H1"

        # get arrays
        self.arr = arrays.Arrays(filename)
        self.loadArrays(filename)

    # load new arrays
    def loadArrays(self,filename):
        # load arrays from file
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
    def getmaxpoint(self,decay):

        # get cross-section times branching ratio
        xb = self.getxb(decay)

        # get index of maximum xsec times BR
        maxidx = np.argmax(xb)

        # get max xsec times BR
        maxxb = xb[maxidx]

        # get theta and vev values that maximize xsec times BR
        maxthS = self.thetahS[maxidx]
        maxthX = self.thetahX[maxidx]
        maxtSX = self.thetaSX[maxidx]
        maxvs = self.vs[maxidx]
        maxvx = self.vx[maxidx]

        return Point(xb=maxxb,
                     tHS=maxthS,
                     tHX=maxthX,
                     tSX=maxtSX,
                     vs=maxvs,
                     vx=maxvx)

    # get the maximum xb
    def getxb(self,decay):

        # get production cross section
        xb_prod = self.getxbprod()

        # get branching ratio
        xb_decay = self.getxbdecay(decay)

        # get total xsec times BR
        xb = np.multiply(xb_prod,xb_decay)

        return xb

    # get maximum xb for the production
    def getxbprod(self):

        # TODO: take decay as argument for other channels modes

        # get production cross section
        xb_prod = np.multiply(self.x_X_gg,self.b_X_SH)

        return xb_prod

    # get maximum xb for the decay
    def getxbdecay(self,decay):

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

        return xb_decay

    def getparams(self):

        minthS = np.min(self.thetahS)
        maxthS = np.max(self.thetahS)
        minthX = np.min(self.thetahX)
        maxthX = np.max(self.thetahX)
        mintSX = np.min(self.thetaSX)
        maxtSX = np.max(self.thetaSX)

        minvs = np.min(self.vs)
        maxvs = np.max(self.vs)
        minvx = np.min(self.vx)
        maxvx = np.max(self.vx)

        return minthS, maxthS, minthX, maxthX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx
    
    def getvars(self):
        return self.thetahS, self.thetahX, self.thetaSX, self.vs, self.vx

    # apply filters as mask
    def getFilteredArrays(self):
        
        # get array of filters to use as a mask
        self.getFilters()

        # create local arrays by applying filter mask

        # theta and vev values
        self.thetahS = self.arr.data['thetahS'][self.filters != 0]
        self.thetahX = self.arr.data['thetahX'][self.filters != 0]
        self.thetaSX = self.arr.data['thetaSX'][self.filters != 0]
        self.vs = self.arr.data['vs'][self.filters != 0]
        self.vx = self.arr.data['vx'][self.filters != 0]

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

class Point:

    def __init__(self,xb=0,tHS=0,tHX=0,tSX=0,vs=0,vx=0):
        self.xb = xb
        self.tHS = tHS
        self.tHX = tHX
        self.tSX = tSX
        self.vs = vs
        self.vx = vx

    # get difference between two values of varname
    def diff(self,other,varname):
        return getattr(self,varname) - getattr(other,varname)

    # get fractional difference between two values of varname
    # TODO: Add divide-by-zero protection
    def diffFrac(self,other,varname):
        return self.diff(self,other,varname) / abs(getattr(self,varname))

    # define the greater than (>) operator
    def __gt__(self,other):
        return self.xb > other.xb

    # define the less than (<) operator
    def __lt__(self,other):
        return self.xb < other.xb
