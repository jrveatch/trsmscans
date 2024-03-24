# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import math
import math

# import tools
import bounds
import width
import arrays

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
args = vars(parser.parse_args())

# Masses
mH1 = 125
mH2 = args["SMass"]
mH3 = args["XMass"]

# maximum allowed width
maxwidth = args["widthmax"]

# number of scan points
npoints = args["npoints"]

# min and max theta values
thetamin = -1 * math.pi / 2
thetamax = math.pi / 2

# min and max vev values
vmin = 0.0
vmax = 1000.0

# names of .ini and .tsv files
base = "TRSMBroken"
templatename = base + "_template.ini"
outbase = "./" + base
ininame = outbase + ".ini"
tsvname = outbase + "_RAW.tsv"
finaltsvname = outbase + "_prescan.tsv"

# read in template .ini file
template = open(templatename,"r")
templatedata = template.read()
template.close()

# directory where we want the output to go
dir = "output/prescan/X"+str(mH3)+"_S"+str(mH2)

# check if directory exists, otherwise make it
if not os.path.exists(dir):
   os.makedirs(dir)

# go into the run directory
os.chdir(dir)

# if a previous prescan exists, check the number of lines
# only rerun if the new prescan is appreciably larger
if os.path.exists(finaltsvname):
    with open(finaltsvname, 'r') as fp:
        num_lines = len(fp.readlines())
        if num_lines > npoints / 2:
            print("Already found a prescan",finaltsvname,"with",num_lines-1,"points.")
            print("If you want to run again, use at least 2x more points. Exiting.")
            quit()

# replace template .ini information with values
filedata = templatedata
filedata = filedata.replace("MH1",str(mH1))
filedata = filedata.replace("MH2",str(mH2))
filedata = filedata.replace("MH3",str(mH3))
filedata = filedata.replace("T1LOW",str(thetamin))
filedata = filedata.replace("T1HIGH",str(thetamax))
filedata = filedata.replace("T2LOW",str(thetamin))
filedata = filedata.replace("T2HIGH",str(thetamax))
filedata = filedata.replace("T3LOW",str(thetamin))
filedata = filedata.replace("T3HIGH",str(thetamax))
filedata = filedata.replace("VSLOW",str(vmin))
filedata = filedata.replace("VSHIGH",str(vmax))
filedata = filedata.replace("VXLOW",str(vmin))
filedata = filedata.replace("VXHIGH",str(vmax))

# write output .ini file
outfile = open(ininame,"w")
outfile.write(filedata)
outfile.close()

# run scan
process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n", str(npoints)]
print(process)
subprocess.run(process)

# rename output .tsv to use prescan name
os.rename(base + ".tsv", tsvname)

# get headers from .tsv file
arrs = arrays.Arrays(tsvname)
headers = arrs.getHeaders()

# run width filter
width.filterwidths(outbase,headers,maxwidth)

# run bounds filter
bounds.filterbounds(outbase,headers,maxwidth)

# copy bounds file to a final file name
shutil.copyfile(tsvname, finaltsvname)

scanend = time.time()

scantime = (scanend - scanstart)

print("Prescan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")
