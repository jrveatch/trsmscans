
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
        self.arr.loadArrays(filename)

    # get the arrays
    def getArrays(self):
        return self.arr

    # find the point that maximizes xb
    def getmaxpoint(self,decay):

        # get cross-section times branching ratio
        xb = self.getxb(decay)

        # get index of maximum xsec times BR
        maxidx = np.argmax(xb)

        # get max xsec times BR
        maxxb = xb[maxidx]

        # get theta and vev values that maximize xsec times BR
        maxthS = self.arr.data['thetahS'][maxidx]
        maxthX = self.arr.data['thetahX'][maxidx]
        maxtSX = self.arr.data['thetaSX'][maxidx]
        maxvs = self.arr.data['vs'][maxidx]
        maxvx = self.arr.data['vx'][maxidx]

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
        xb_prod = np.multiply(self.arr.data['x_H3_gg'],self.arr.data['b_H3_H1H2'])

        return xb_prod

    # get maximum xb for the decay
    def getxbdecay(self,decay):

        match decay:
            case "H2bbH1tautau":
                xb_decay = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_bb'])
            case "H2tautauH1bb":
                xb_decay = np.multiply(self.arr.data['b_H1_bb'],self.arr.data['b_H2_tautau'])
            case "H2H1bbtautau":
                arr1 = np.multiply(self.arr.data['b_H1_bb'],self.arr.data['b_H2_tautau'])
                arr2 = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_bb'])
                xb_decay = np.add(arr1,arr2)
            case "H2WWH1tautau":
                xb_decay = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_WW'])
            case "H2tautauH1WW":
                xb_decay = np.multiply(self.arr.data['b_H2_tautau'],self.arr.data['b_H1_WW'])
            case "H2H1WWtautau":
                arr1 = np.multiply(self.arr.data['b_H2_tautau'],self.arr.data['b_H1_WW'])
                arr2 = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_WW'])
                xb_decay = np.add(arr1,arr2)
            case "H2ZZH1tautau":
                xb_decay = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_ZZ'])
            case "H2tautauH1ZZ":
                xb_decay = np.multiply(self.arr.data['b_H2_tautau'],self.arr.data['b_H1_ZZ'])
            case "H2H1ZZtautau":
                arr1 = np.multiply(self.arr.data['b_H2_tautau'],self.arr.data['b_H1_ZZ'])
                arr2 = np.multiply(self.arr.data['b_H1_tautau'],self.arr.data['b_H2_ZZ'])
                xb_decay = np.add(arr1,arr2)
            case "H2VVH1tautau":
                xb_decay = np.multiply(self.arr.data['b_H1_tautau'],np.add(self.arr.data['b_H2_WW'],self.arr.data['b_H2_ZZ']))
            case "H2tautauH1VV":
                xb_decay = np.multiply(self.arr.data['b_H2_tautau'],np.add(self.arr.data['b_H1_WW'],self.arr.data['b_H1_ZZ']))
            case "H2H1VVtautau":
                arr1 = np.multiply(self.arr.data['b_H2_tautau'],np.add(self.arr.data['b_H1_WW'],self.arr.data['b_H1_ZZ']))
                arr2 = np.multiply(self.arr.data['b_H1_tautau'],np.add(self.arr.data['b_H2_WW'],self.arr.data['b_H2_ZZ']))
                xb_decay = np.add(arr1,arr2)
            case _:
                print("Unrecognized decay",decay)
                print("This should not have happened")
                quit()

        return xb_decay

    def getparams(self):

        minthS = np.min(self.arr.data['thetahS'])
        maxthS = np.max(self.arr.data['thetahS'])
        minthX = np.min(self.arr.data['thetahX'])
        maxthX = np.max(self.arr.data['thetahX'])
        mintSX = np.min(self.arr.data['thetaSX'])
        maxtSX = np.max(self.arr.data['thetaSX'])

        minvs = np.min(self.arr.data['vs'])
        maxvs = np.max(self.arr.data['vs'])
        minvx = np.min(self.arr.data['vx'])
        maxvx = np.max(self.arr.data['vx'])

        return minthS, maxthS, minthX, maxthX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx
    
    def getvars(self):
        
        return self.arr.data['thetahS'], self.arr.data['thetahX'], self.arr.data['thetaSX'], self.arr.data['vs'], self.arr.data['vx']
