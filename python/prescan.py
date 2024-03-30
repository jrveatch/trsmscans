# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import tools
import params
import filters
import runScannerS

def runPrescan():

    # get scan start time
    scanstart = time.time()

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", default=500, type=int, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", default=300, type=int, help="Mass of scalar S in GeV")
    argparser.add_argument("-n", "--npoints", default=50000, type=int, help="Initial number of scan points")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    args = vars(argparser.parse_args())

    # Masses
    HMass = 125
    SMass = args["SMass"]
    XMass = args["XMass"]

    # maximum allowed width
    maxwidth = args["widthmax"]

    # number of scan points
    npoints = args["npoints"]

    # overwrite previous prescan
    overwrite = args['overwrite']

    # TODO: Add check to make sure overwrite is wanted

    # whether multiprocessing should be used
    use_multiprocessing = args['multiprocessing']

    # make instance of params
    # this automatically initializes the parameters
    pars = params.Params(HMass,SMass,XMass)

    # names of .ini and .tsv files
    base = "TRSMBroken"
    initemplate = base + "_template.ini"
    outbase = "./" + base
    ininame = outbase + ".ini"
    tsvname_initial = outbase + ".tsv"
    tsvname = outbase + "_prescan.tsv"

    # get prescan directory
    prescandir = os.environ['PRESCANDIR']

    # directory where we want the output to go
    dir = prescandir+"/X"+str(XMass)+"_S"+str(SMass)

    # remove previous directory if set to overwrite
    if os.path.exists(dir) and overwrite:
        shutil.rmtree(dir)

    # check if directory exists, if not make it
    if not os.path.exists(dir):
        os.makedirs(dir)

    # copy template .ini into dir
    shutil.copy(initemplate,dir)

    # go into the run directory
    os.chdir(dir)

    # get number of pre-existing prescan points
    nexisting = checkPrescan(XMass=XMass,SMass=SMass)

    # boolean indicating whether prescan already exists
    prescan_exists = False

    # if prescan exists, adjust the number of prescan points to run
    if nexisting >= 0:
        prescan_exists = True

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

    # write .ini file from template
    pars.writeini(initemplate,ininame)

    # run ScannerS
    if use_multiprocessing:
        runScannerS.runParallelProcesses(ininame,npoints)
    else:
        runScannerS.runSingleProcess(ininame,npoints)

    # initialize filter columns
    filters.initializeFilters(tsvname_initial)

    # if prescan does not already exist, rename file
    if not prescan_exists:
        os.rename(tsvname_initial,tsvname)
    # otherwise append new file to existing prescan .tsv
    else:
        with open(tsvname_initial,'r') as source_file:
            # skip the first line
            next(source_file)

            # open final .tsv file for appending
            with open(tsvname,'a') as destination_file:
                # get each line in the new .tsv file
                for line in source_file:
                    # replace the index with a unique value
                    parts = line.strip().split('\t')
                    parts[0] = str(int(parts[0]) + nexisting)
                    # append each line to final .tsv file
                    destination_file.write('\t'.join(parts) + '\n')

        # delete new .tsv file
        os.remove(tsvname_initial)

    # apply width and bounds filters
    # this also renames the output .tsv file
    filters.applyFilters(tsvname,maxwidth=maxwidth)

    # get total time taken
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    return 0

# function to check previous prescan
# returns -1 if previous prescan does not exist
# otherwise returns number of existing prescan points
def checkPrescan(XMass,SMass):

    # get prescan directory
    prescandir = os.environ['PRESCANDIR']

    # prescan file name
    filename = prescandir+"/X"+str(XMass)+"_S"+str(SMass)+"/TRSMBroken_prescan.tsv"

    # if file doesn't exist, return -1
    if not os.path.exists(filename):
        print(filename,"does not exist yet.")
        return -1

    # run wc -l to get the number of lines
    result = subprocess.run(["wc", "-l", filename], capture_output=True, text=True)

    # get output from wc -l
    output = result.stdout.strip()

    # get the number of previously scanned points
    npoints = int(output.split()[0]) - 1

    return npoints

if __name__ == "__main__":
    runPrescan()
