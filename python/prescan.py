#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse

# import package tools
from filters.filter import apply_filters, initialize_filters
from utils.runScannerS import runScannerS
from utils import tsvutils
from utils import fileutils
from utils.params import Params
from utils.masses import Masses

# TODO: Make this return a Parse object
def run_prescan(masses: 'Masses',
                modelname: str,
                npoints: int,
                maxwidth: float,
                overwrite: bool = False,
                use_multiprocessing: bool = False) -> int:

    # get scan start time
    scanstart = time.time()

    # directory where we want the output to go
    outdir = fileutils.prescan_dir(modelname=modelname,
                                   masses=masses)

    # names of .ini and .tsv files
    ininame = outdir + modelname + ".ini"
    tsvname_initial = outdir + modelname + ".tsv"
    tsvname = outdir + modelname + "_prescan.tsv"

    # print starting message
    print("\nRunning a prescan with",npoints,"points for",str(masses))

    # get number of pre-existing prescan points
    nexisting = tsvutils.count_tsv_points(tsvname)

    # if requested points are < 20% of existing points, request confirmation to overwrite
    if overwrite and npoints < nexisting * 0.2:
        print("You are requesting",npoints,"points but there are already",nexisting,"points")
        while True:
            # get user response
            response = input("Are you sure you want to overwrite the existing prescan? (yes/no): ").strip().lower()
            # if yes, print message and break out of while loop
            if response in ["yes", "y"]:
                print("Overwriting existing prescan")
                break
            # if no, print message and return
            elif response in ["no", "n"]:
                print("Exiting prescan")
                return 0
            # complain if response is neither yes nor no
            else:
                print("Please enter 'yes' or 'no'.")

    # remove previous directory if set to overwrite
    if os.path.exists(outdir) and overwrite:
        # remove directory
        shutil.rmtree(outdir)
        # reset nexisting to 0
        nexisting = 0

    # if prescan exists, adjust the number of prescan points to run
    if nexisting > 0:

        # if enough points already exist, exit
        if nexisting >= npoints:
            print("Found a prescan that already has",nexisting,"points.")
            print(npoints,"points request, skipping since no more are needed.")
            print("If you want to overwrite the existing prescan, run with the -o option.")
            return 0

        # otherwise reduce the number of points to run with
        npointsOld = npoints
        npoints -= nexisting
        print("Found prescan with",nexisting,"points.")
        print(npointsOld,"prescan points requested, so I am running with",npoints,"points.")
        print("If you want to overwrite the existing prescan, run with the -o option.")

    # check if directory exists, if not make it
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # store starting directory
    startDir = os.getcwd()

    # move into working directory for prescan
    os.chdir(outdir)

    # print location
    print("Running prescan in",outdir)

    # make instance of params
    # this automatically initializes the parameters
    params = Params(modelname,masses)

    # write .ini file from template
    params.write_ini(ininame)

    # run ScannerS to sample points
    try:
        runScannerS(ininame=ininame,
                    modelname=modelname,
                    npoints=npoints,
                    use_multiprocessing=use_multiprocessing)

    # if timeout error is caught, delete the directory and raise
    except TimeoutError:

        # delete directory
        shutil.rmtree(outdir)

        # return result from process
        raise

    # make sure new .tsv has filter columns
    initialize_filters(filename=tsvname_initial)

    # save output to tsvname
    tsvutils.save_tsv_output(inputfile=tsvname_initial,
                             outputfile=tsvname)

    # apply width and bounds filters
    apply_filters(filename=tsvname,
                  masses=masses,
                  modelname=modelname,
                  maxwidth=maxwidth)

    # get total time taken
    scanend = time.time()
    scantime = (scanend - scanstart)

    # move back to the starting directory
    os.chdir(startDir)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    # return after a successful run
    return 0

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    argparser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    argparser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")
    argparser.add_argument("-w", "--maxwidth", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Use if multiprocessing should be used")
    args = argparser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    run_prescan(masses=masses,
                modelname=args.model,
                npoints=args.npoints,
                maxwidth=args.maxwidth,
                overwrite=args.overwrite,
                use_multiprocessing=args.multiprocessing)
