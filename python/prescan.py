# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import tools
from params import Params
import filters
import runScannerS
from masses import Masses
import tsvutils

def runPrescan(masses: 'Masses',
               modelname,
               npoints,
               maxwidth,
               overwrite=False,
               use_multiprocessing=False,
               stepsize=10000):

    # get scan start time
    scanstart = time.time()

    # TODO: Add check to make sure overwrite is wanted

    # get prescan directory
    prescandir = os.environ['OUTPUTDIR'] + modelname + "/prescan/"

    # directory where we want the output to go
    outdir = prescandir+str(masses)+"/"

    # names of .ini and .tsv files
    ininame = outdir + modelname + ".ini"
    tsvname_initial = outdir + modelname + ".tsv"
    tsvname = outdir + modelname + "_prescan.tsv"

    # print starting message
    print("\nRunning a prescan with",npoints,"points for",str(masses))
    print("Running in",outdir)

    # remove previous directory if set to overwrite
    if os.path.exists(outdir) and overwrite:
        shutil.rmtree(outdir)

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

    # get number of pre-existing prescan points
    nexisting = checkPrescan(masses,modelname)

    # if prescan exists, adjust the number of prescan points to run
    if nexisting >= 0:

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
    if stepsize > 0:

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
    # this also renames the output .tsv file
    filters.applyFilters(tsvname,maxwidth=maxwidth,masses=masses)

    # get total time taken
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    # return after a successful run
    return 0

# function to check previous prescan
def checkPrescan(masses: Masses,modelname):

    # get prescan directory
    prescandir = os.environ['OUTPUTDIR'] + modelname + "/prescan/"

    # prescan file name
    filename = prescandir+"/"+str(masses)+"/"+modelname+"_prescan.tsv"

    # get number of points in file
    npoints = tsvutils.countPointsInTSV(filename)

    return npoints

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
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Use if multiprocessing should be used")
    argparser.add_argument("-t", "--stepsize", default=10000, type=int, help="Step size to save progress")
    args = vars(argparser.parse_args())

    # masses
    xmass = args["XMass"]
    smass = args["SMass"]
    hmass = args["HMass"]

    # create masses object
    masses = Masses(mX=xmass,mS=smass,mH=hmass)

    # model name
    modelname = args['model']

    # number of points to run
    npoints = args["npoints"]

    # progress saving step size
    stepsize = args["stepsize"]

    # get maximum width
    maxwidth = args["widthmax"]

    # run options
    overwrite = args["overwrite"]
    use_multiprocessing = args["multiprocessing"]

    runPrescan(masses=masses,
               modelname=modelname,
               npoints=npoints,
               maxwidth=maxwidth,
               overwrite=overwrite,
               use_multiprocessing=use_multiprocessing,
               stepsize=stepsize)
