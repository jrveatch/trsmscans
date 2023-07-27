# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import argparse

# import math
import math

# import tools
import bounds
import width
import columns

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
#thetamin = 0
#thetamax = 2*math.pi

# min and max vev values
vmin = 0.0
vmax = 1000.0

base = "TRSMBroken"
tempname = base + "_template.ini"

template = open(tempname,"r")
templatedata = template.read()
template.close()

# directory where we want to run
dir = "output/prescan/X"+str(mH3)+"_S"+str(mH2)

# check if directory exists, otherwise make it
if not os.path.exists(dir):
   os.makedirs(dir)

# go into the run directory
os.chdir(dir)

outname = "./" + base

num_lines = 0

if os.path.exists(outname + "_RAW.tsv"):
    with open(outname + "_RAW.tsv", "r") as f:
        num_lines = sum(1 for _ in f)

if num_lines > 1.1 * npoints:
    print("Already found a prescan with",num_lines-1,"points.")
    print("If you want to run again, use at least 10% more points. Exiting.")
    quit()

ininame = outname + ".ini"
tsvname = outname + "_RAW.tsv"

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

outfile = open(ininame,"w")
outfile.write(filedata)
outfile.close()

if not os.path.exists(outname + "_COLS.tsv"):
    print("No COLS file found, creating one")
    process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n 1"]
    print(process)
    subprocess.run(process)
    os.rename(base + ".tsv", base + "_COLS.tsv")

# get list of column numbers
cols = columns.Columns(outname + "_COLS.tsv")

process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n", str(npoints)]
print(process)
subprocess.run(process)

os.rename(base + ".tsv", tsvname)

# run width filter
width.filterwidths(outname,cols,maxwidth)

# run bounds filter
bounds.filterbounds(outname,cols,maxwidth)

# copy bounds file to a final file name
shutil.copyfile(outname + "_RAW.tsv", outname + "_prescan.tsv")

scanend = time.time()

scantime = (scanend - scanstart)

print("Prescan took",f"{scantime:1.1f}","seconds")

