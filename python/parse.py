
# import numpy library as np
import numpy as np

# import list of arrays
import arrays

def getmaxpoint(arr:arrays.Arrays,decay):

    # get production cross section
    xb_prod = np.multiply(arr.x_H3_gg,arr.b_H3_H1H2)

    # get branching ratio
    ##### TODO: Need to modify this to use decay mode options

    match decay:
        case "H2bbH1tautau":
            xb_decay = np.multiply(arr.b_H1_tautau,arr.b_H2_bb)
        case "H2tautauH1bb":
            xb_decay = np.multiply(arr.b_H1_bb,arr.b_H2_tautau)
        case "H2H1bbtautau":
            arr1 = np.multiply(arr.b_H1_bb,arr.b_H2_tautau)
            arr2 = np.multiply(arr.b_H1_tautau,arr.b_H2_bb)
            xb_decay = np.add(arr1,arr2)
        case "H2WWH1tautau":
            xb_decay = np.multiply(arr.b_H1_tautau,arr.b_H2_WW)
        case "H2tautauH1WW":
            xb_decay = np.multiply(arr.b_H2_tautau,arr.b_H1_WW)
        case "H2H1WWtautau":
            arr1 = np.multiply(arr.b_H2_tautau,arr.b_H1_WW)
            arr2 = np.multiply(arr.b_H1_tautau,arr.b_H2_WW)
            xb_decay = np.add(arr1,arr2)
        case "H2ZZH1tautau":
            xb_decay = np.multiply(arr.b_H1_tautau,arr.b_H2_ZZ)
        case "H2tautauH1ZZ":
            xb_decay = np.multiply(arr.b_H2_tautau,arr.b_H1_ZZ)
        case "H2H1ZZtautau":
            arr1 = np.multiply(arr.b_H2_tautau,arr.b_H1_ZZ)
            arr2 = np.multiply(arr.b_H1_tautau,arr.b_H2_ZZ)
            xb_decay = np.add(arr1,arr2)
        case "H2VVH1tautau":
            xb_decay = np.multiply(arr.b_H1_tautau,np.add(arr.b_H2_WW,arr.b_H2_ZZ))
        case "H2tautauH1VV":
            xb_decay = np.multiply(arr.b_H2_tautau,np.add(arr.b_H1_WW,arr.b_H1_ZZ))
        case "H2H1VVtautau":
            arr1 = np.multiply(arr.b_H2_tautau,np.add(arr.b_H1_WW,arr.b_H1_ZZ))
            arr2 = np.multiply(arr.b_H1_tautau,np.add(arr.b_H2_WW,arr.b_H2_ZZ))
            xb_decay = np.add(arr1,arr2)
        case _:
            print("Unrecognized decay",decay)
            print("This should not have happened")
            quit()

    # get total xsec times BR
    xb = np.multiply(xb_prod,xb_decay)

    # get index of maximum xsec times BR
    maxidx = np.argmax(xb)

    # get max xsec times BR
    maxxb = xb[maxidx]

    # get theta and vev values that maximize xsec times BR
    maxthS = arr.thetahS[maxidx]
    maxthX = arr.thetahX[maxidx]
    maxtSX = arr.thetaSX[maxidx]
    maxvs = arr.vs[maxidx]
    maxvx = arr.vx[maxidx]

    return maxxb, maxidx, maxthS, maxthX, maxtSX, maxvs, maxvx

def getranges(arr:arrays.Arrays):

    minthS = np.min(arr.thetahS)
    maxthS = np.max(arr.thetahS)
    minthX = np.min(arr.thetahX)
    maxthX = np.max(arr.thetahX)
    mintSX = np.min(arr.thetaSX)
    maxtSX = np.max(arr.thetaSX)

    minvs = np.min(arr.vs)
    maxvs = np.max(arr.vs)
    minvx = np.min(arr.vx)
    maxvx = np.max(arr.vx)

    return minthS, maxthS, minthX, maxthX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx
