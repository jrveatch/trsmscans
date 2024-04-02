
# import numpy library as np
import numpy as np

# import list of arrays
import arrays

class Parse:

    # load new set of arrays
    def __init__(self,filename):
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

        return maxxb, maxthS, maxthX, maxtSX, maxvs, maxvx

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
        xb_prod = np.multiply(self.x_H3_gg,self.b_H3_H1H2)

        return xb_prod

    # get maximum xb for the decay
    def getxbdecay(self,decay):

        # get appropriate BR for decay mode
        match decay:

            # 4b case
            case "H2H1bbbb":
                xb_decay = np.multiply(self.b_H1_bb,self.b_H2_bb)

            # bbtautau cases
            case "H2bbH1tautau":
                xb_decay = np.multiply(self.b_H1_tautau,self.b_H2_bb)
            case "H2tautauH1bb":
                xb_decay = np.multiply(self.b_H1_bb,self.b_H2_tautau)
            case "H2H1bbtautau":
                arr1 = np.multiply(self.b_H1_bb,self.b_H2_tautau)
                arr2 = np.multiply(self.b_H1_tautau,self.b_H2_bb)
                xb_decay = np.add(arr1,arr2)

            # bbWW cases
            case "H2bbH1WW":
                xb_decay = np.multiply(self.b_H1_WW,self.b_H2_bb)
            case "H2WWH1bb":
                xb_decay = np.multiply(self.b_H2_WW,self.b_H1_bb)
            case "H2H1bbWW":
                arr1 = np.multiply(self.b_H2_WW,self.b_H1_bb)
                arr2 = np.multiply(self.b_H1_WW,self.b_H2_bb)
                xb_decay = np.add(arr1,arr2)

            # bbZZ cases
            case "H2bbH1ZZ":
                xb_decay = np.multiply(self.b_H1_ZZ,self.b_H2_bb)
            case "H2ZZH1bb":
                xb_decay = np.multiply(self.b_H2_ZZ,self.b_H1_bb)
            case "H2H1bbZZ":
                arr1 = np.multiply(self.b_H2_ZZ,self.b_H1_bb)
                arr2 = np.multiply(self.b_H1_ZZ,self.b_H2_bb)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "H2VVH1bb":
                xb_decay = np.multiply(self.b_H1_bb,np.add(self.b_H2_WW,self.b_H2_ZZ))
            case "H2bbH1VV":
                xb_decay = np.multiply(self.b_H2_bb,np.add(self.b_H1_WW,self.b_H1_ZZ))
            case "H2H1VVbb":
                arr1 = np.multiply(self.b_H2_bb,np.add(self.b_H1_WW,self.b_H1_ZZ))
                arr2 = np.multiply(self.b_H1_bb,np.add(self.b_H2_WW,self.b_H2_ZZ))
                xb_decay = np.add(arr1,arr2)

            # WWtautau cases
            case "H2WWH1tautau":
                xb_decay = np.multiply(self.b_H1_tautau,self.b_H2_WW)
            case "H2tautauH1WW":
                xb_decay = np.multiply(self.b_H2_tautau,self.b_H1_WW)
            case "H2H1WWtautau":
                arr1 = np.multiply(self.b_H2_tautau,self.b_H1_WW)
                arr2 = np.multiply(self.b_H1_tautau,self.b_H2_WW)
                xb_decay = np.add(arr1,arr2)

            # ZZtautau cases
            case "H2ZZH1tautau":
                xb_decay = np.multiply(self.b_H1_tautau,self.b_H2_ZZ)
            case "H2tautauH1ZZ":
                xb_decay = np.multiply(self.b_H2_tautau,self.b_H1_ZZ)
            case "H2H1ZZtautau":
                arr1 = np.multiply(self.b_H2_tautau,self.b_H1_ZZ)
                arr2 = np.multiply(self.b_H1_tautau,self.b_H2_ZZ)
                xb_decay = np.add(arr1,arr2)

            # VVtautau cases
            case "H2VVH1tautau":
                xb_decay = np.multiply(self.b_H1_tautau,np.add(self.b_H2_WW,self.b_H2_ZZ))
            case "H2tautauH1VV":
                xb_decay = np.multiply(self.b_H2_tautau,np.add(self.b_H1_WW,self.b_H1_ZZ))
            case "H2H1VVtautau":
                arr1 = np.multiply(self.b_H2_tautau,np.add(self.b_H1_WW,self.b_H1_ZZ))
                arr2 = np.multiply(self.b_H1_tautau,np.add(self.b_H2_WW,self.b_H2_ZZ))
                xb_decay = np.add(arr1,arr2)

            # bbgamgam cases
            case "H2bbH1gamgam":
                xb_decay = np.multiply(self.b_H1_gamgam,self.b_H2_bb)
            case "H2gamgamH1bb":
                xb_decay = np.multiply(self.b_H1_bb,self.b_H2_gamgam)
            case "H2H1bbgamgam":
                arr1 = np.multiply(self.b_H1_bb,self.b_H2_gamgam)
                arr2 = np.multiply(self.b_H1_gamgam,self.b_H2_bb)
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
        self.b_H1_bb = self.arr.data['b_H1_bb'][self.filters != 0]
        self.b_H1_tautau = self.arr.data['b_H1_tautau'][self.filters != 0]
        self.b_H1_WW = self.arr.data['b_H1_WW'][self.filters != 0]
        self.b_H1_ZZ = self.arr.data['b_H1_ZZ'][self.filters != 0]
        self.b_H1_gamgam = self.arr.data['b_H1_gamgam'][self.filters != 0]

        # H2 xsec and BR values
        self.b_H2_bb = self.arr.data['b_H2_bb'][self.filters != 0]
        self.b_H2_tautau = self.arr.data['b_H2_tautau'][self.filters != 0]
        self.b_H2_WW = self.arr.data['b_H2_WW'][self.filters != 0]
        self.b_H2_ZZ = self.arr.data['b_H2_ZZ'][self.filters != 0]
        self.b_H2_gamgam = self.arr.data['b_H2_gamgam'][self.filters != 0]

        # H3 xsec and BR values
        self.x_H3_gg = self.arr.data['x_H3_gg'][self.filters != 0]
        self.b_H3_H1H2 = self.arr.data['b_H3_H1H2'][self.filters != 0]
