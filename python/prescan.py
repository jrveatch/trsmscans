#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import package tools
import filters
import runScannerS
from utils import tsvutils
from utils import fileutils
from params import Params
from masses import Masses

def runPrescan(masses: 'Masses',
               modelname,
               npoints,
               maxwidth,
               overwrite=False,
               use_multiprocessing=False,
               stepsize=10000):

    # get scan start time
    scanstart = time.time()

    # directory where we want the output to go
    outdir = fileutils.prescanDir(modelname=modelname,masses=masses)

    # names of .ini and .tsv files
    ininame = outdir + modelname + ".ini"
    tsvname_initial = outdir + modelname + ".tsv"
    tsvname = outdir + modelname + "_prescan.tsv"

    # print starting message
    print("\nRunning a prescan with",npoints,"points for",str(masses))
    print("Running in",outdir)

    # get number of pre-existing prescan points
    nexisting = checkPrescan(tsvname)

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

    # check if directory exists, if not make it
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # move into working directory for prescan
    os.chdir(outdir)

    # make instance of params
    # this automatically initializes the parameters
    params = Params(modelname,masses)

    # write .ini file from template
    params.writeini(ininame)

    # if prescan exists, adjust the number of prescan points to run
    if nexisting > 0:

        # if enough points already exist, exit
        if nexisting >= npoints:
            print("Found a prescan that already has",nexisting,"points.")
            print(npoints,"points request, skipping since no more are needed.")
            print("If you want to overwrite the existing prescan, run with -o.")
            return 0

        # otherwise reduce the number of points to run with
        npointsOld = npoints
        npoints -= nexisting
        print("Found prescan with",nexisting,"points.")
        print(npointsOld,"prescan points requested, so I am running with",npoints,"points.")
        print("If you want to overwrite the existing prescan, run with -o.")

    # increment up to the total number of points this will
    # run the prescan to add stepsize points each time
    # this approach takes a slightly longer time but allows
    # progress to be captured at smaller increments in case
    # the longer prescan runs get interrupted

    # number of points that have already been run
    points_done = 0

    # keep going while fewer than npoints have been done so far
    while points_done < npoints:

        # if there is space, run another set of stepsize
        if npoints - points_done > stepsize:
            points_to_run = stepsize

        # otherwise run the remaining points
        else:
            points_to_run = npoints - points_done

        # run ScannerS for the next set of points
        if use_multiprocessing:
            result = runScannerS.runParallelProcesses(ininame=ininame,
                                                      modelname=modelname,
                                                      npoints=points_to_run)
        else:
            result = runScannerS.runSingleProcess(ininame=ininame,
                                                  modelname=modelname,
                                                  npoints=points_to_run)

        # if a process returns a negative result, delete directory and return result
        if result < 0:

            # inform user
            print("Removing directory",outdir)

            # delete directory
            shutil.rmtree(outdir)

            # return result from process
            return result

        # increment the count of points done
        points_done += tsvutils.countPointsInTSV(tsvname_initial)

        # initialize filter columns
        filters.initializeFilters(tsvname_initial)

        # save output to tsvname
        tsvutils.saveTSVOutput(inputfile=tsvname_initial,
                               outputfile=tsvname)

    # apply width and bounds filters
    filters.applyFilters(filename=tsvname,
                         masses=masses,
                         modelname=modelname,
                         maxwidth=maxwidth)

    # get total time taken
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    # return after a successful run
    return 0

# function to check previous prescan
def checkPrescan(tsvname):

    # get number of points in file
    return tsvutils.countPointsInTSV(tsvname)

# function to get number of points in a file
# returns -1 if file does not exist
# otherwise returns number of existing points in file
def countNPointsInFile(filename):

    # if file doesn't exist, return -1
    if not os.path.exists(filename):
        return -1

    # run wc -l to get the number of lines
    result = subprocess.run(["wc", "-l", filename], capture_output=True, text=True)

    # get output from wc -l
    output = result.stdout.strip()

    # get the number of previously scanned points
    npoints = int(output.split()[0]) - 1

    # return number of points
    return npoints

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
    argparser.add_argument("-t", "--stepsize", default=10000, type=int, help="Step size to save progress")
    args = argparser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    runPrescan(masses=masses,
               modelname=args.model,
               npoints=args.npoints,
               maxwidth=args.maxwidth,
               overwrite=args.overwrite,
               use_multiprocessing=args.multiprocessing,
               stepsize=args.stepsize)
