
import os
import prescan
import argparse

def runAllPrescans(npoints,
                   maxwidth,
                   overwrite=False,
                   use_multiprocessing=True):

    # get the data directory
    datadir = os.environ['DATADIR']

    # file with list of mass points
    masspointsfile = datadir+"/masspoints.txt"

    # open mass points file
    with open(masspointsfile,"r") as masspoints:

        # read the rest of the file
        for line in masspoints:

            # skip any lines that are commented out
            if line.startswith('#'):
                continue

            # parse the line and store the mass values
            xmass, smass = line.strip().split()

            # print info to screen
            print("\n\nRunning prescan for XMass =",xmass,"SMass =",smass)

            # run a prescan for each mass point
            result = prescan.runPrescan(XMass=float(xmass),
                                        SMass=float(smass),
                                        npoints=npoints,
                                        maxwidth=maxwidth,
                                        overwrite=overwrite,
                                        use_multiprocessing=use_multiprocessing)

            # print error to screen
            if result < 0:
                print("mX = ",xmass,"mS =",smass,"has timed out. It is probably best to not use it.")

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-n", "--npoints", default=50000, type=int, help="Initial number of scan points")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    argparser.add_argument("-s", "--single_process", action="store_true", help="Use if multiprocessing should not be used")
    args = vars(argparser.parse_args())

    # number of points to run
    npoints = args["npoints"]

    # get maximum width
    maxwidth = args["widthmax"]

    # run options
    overwrite = args["overwrite"]
    use_single_process = args["single_process"]

    # run all prescans
    runAllPrescans(npoints=npoints,
                   maxwidth=maxwidth,
                   overwrite=overwrite,
                   use_multiprocessing=not use_single_process)
    