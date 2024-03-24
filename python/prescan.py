# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import tools
import bounds
import width
import arrays
import params
import filterinit

# get scan start time
scanstart = time.time()

# get homedirectory
home = os.getcwd()

# Parse command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-X", "--XMass", default=500, type=int, help="Mass of heavy scalar X in GeV")
parser.add_argument("-S", "--SMass", default=300, type=int, help="Mass of scalar S in GeV")
parser.add_argument("-n", "--npoints", default=50000, type=int, help="Initial number of scan points")
parser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
parser.add_argument("-f", "--force", default=False, type=bool, help="Overwrite previous prescan")
args = vars(parser.parse_args())

# Masses
mH1 = 125
mH2 = args["SMass"]
mH3 = args["XMass"]

# maximum allowed width
maxwidth = args["widthmax"]

# number of scan points
npoints = args["npoints"]

# overwrite previous prescan
overwrite = args['force']

# TODO: Add check to make sure overwrite is wanted

# make instance of params
# this automatically initializes the parameters
pars = params.Params(mH1,mH2,mH3)

# names of .ini and .tsv files
base = "TRSMBroken"
initemplate = base + "_template.ini"
outbase = "./" + base
ininame = outbase + ".ini"
tsvname = outbase + "_prescan.tsv"

# directory where we want the output to go
dir = "output/prescan/X"+str(mH3)+"_S"+str(mH2)

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

# if a previous prescan exists, check the number of lines
# only rerun if the new prescan is appreciably larger
if os.path.exists(tsvname):
    with open(tsvname, 'r') as fp:
        num_lines = len(fp.readlines())
        if num_lines > npoints / 2:
            print("Already found a prescan",tsvname,"with",num_lines-1,"points.")
            print("If you want to run again, use at least 2x more points. Exiting.")
            quit()

# write .ini file from template
pars.writeini(initemplate,ininame)

# run scan
process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n", str(npoints)]
print(process)
subprocess.run(process)

# initialize filter columns
# this also renames the output .tsv
filterinit.init_filter_columns(base + ".tsv",tsvname)

# run width filter
width.filterwidths(tsvname,maxwidth)

# run bounds filter
bounds.filterbounds(tsvname,maxwidth)

scanend = time.time()

scantime = (scanend - scanstart)

print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")
