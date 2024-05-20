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

def runPrescan(masses: 'Masses',
               npoints,
               maxwidth,
               overwrite=False,
               use_multiprocessing=False,
               stepsize=10000):

    # get scan start time
    scanstart = time.time()

    # get masses
    XMass = masses.mX
    SMass = masses.mS

    # TODO: Add check to make sure overwrite is wanted

    # names of .ini and .tsv files
    base = "TRSMBroken"
    templateini = base + "_template.ini"
    outbase = "./" + base
    ininame = outbase + ".ini"
    tsvname_initial = outbase + ".tsv"
    tsvname = outbase + "_prescan.tsv"

    # get prescan directory
    prescandir = os.environ['PRESCANDIR']

    # directory where we want the output to go
    dir = prescandir+"/X"+str(XMass)+"_S"+str(SMass)+"/"

    # remove previous directory if set to overwrite
    if os.path.exists(dir) and overwrite:
        shutil.rmtree(dir)

    # check if directory exists, if not make it
    if not os.path.exists(dir):
        os.makedirs(dir)

    # copy template .ini into dir if it doesn't already exist
    if not os.path.exists(dir+templateini):
        shutil.copy(templateini,dir)

    # go into the run directory
    os.chdir(dir)

    # make instance of params
    # this automatically initializes the parameters
    pars = Params(masses)

    # write .ini file from template
    pars.writeini(templateini,ininame)

    # get number of pre-existing prescan points
    nexisting = checkPrescan(masses)

    # if prescan exists, adjust the number of prescan points to run
    if nexisting >= 0:

        # if enough points already exist, exit
        if nexisting >= npoints:
            print("Found a prescan that already has",nexisting,"points.")
            print("Skipping this prescan of",npoints,"points.")
            print("If you want to overwrite the existing prescan, run with -o.")
            return 0

        # otherwise reduce the number of points to run with
        npointsOld = npoints
        npoints -= nexisting
        print("Found prescan with",nexisting,"points.")
        print(npointsOld,"points requested, so I am running with",npoints,"points.")
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
                result = runScannerS.runParallelProcesses(ininame,points_to_run)
            else:
                result = runScannerS.runSingleProcess(ininame,points_to_run)

            # if a process returns a negative result, delete directory and return result
            if result < 0:

                # inform user
                print("Removing directory",dir)

                # delete directory
                shutil.rmtree(dir)

                # return result from process
                return result

            # increment the count of points done
            points_done += countNPointsInFile(tsvname_initial)

            # initialize filter columns
            filters.initializeFilters(tsvname_initial)

            # save output to tsvname
            saveOutput(tsvname_initial,tsvname)

    # apply width and bounds filters
    # this also renames the output .tsv file
    filters.applyFilters(tsvname,maxwidth=maxwidth,masses=masses)

    # get total time taken
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    return 0

# function to check previous prescan
def checkPrescan(masses: Masses):

    # get prescan directory
    prescandir = os.environ['PRESCANDIR']

    # prescan file name
    filename = prescandir+"/X"+str(masses.mX)+"_S"+str(masses.mS)+"/TRSMBroken_prescan.tsv"

    # get number of points in file
    npoints = countNPointsInFile(filename)

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

    return npoints

# function to save output
def saveOutput(inputfile,outputfile):

    # get number of points already in output file
    nexisting = countNPointsInFile(outputfile)

    # if output file doesn't exist or is empty, simply rename input file
    if nexisting <= 0:
        os.rename(inputfile,outputfile)
        return

    # otherwise append the contents of inputfile to outputfile
    with open(inputfile,'r') as source_file:
        # skip the first line
        next(source_file)

        # open output .tsv file for appending
        with open(outputfile,'a') as destination_file:

            # get each line in the new .tsv file
            for line in source_file:

                # replace the index with a unique value
                parts = line.strip().split('\t')
                parts[0] = str(int(parts[0]) + nexisting)

                # append each line to final .tsv file
                destination_file.write('\t'.join(parts) + '\n')

    # delete input .tsv file
    os.remove(inputfile)

    return

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", required=True, type=int, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=int, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125, type=int, help="Mass of scalar H in GeV")
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
               npoints=npoints,
               maxwidth=maxwidth,
               overwrite=overwrite,
               use_multiprocessing=use_multiprocessing,
               stepsize=stepsize)
