# import various modules to help with logistics
import os
import subprocess
import time
import argparse

# import math
import math

# import decimal
from decimal import Decimal

# import tools
import parse
import width
import bounds

import columns

# get scan start time
scanstart = time.time()

# get homedirectory
home = os.getcwd()

# Parse command line arguments
parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
parser.add_argument("-X", "--XMass", default=500, type=int, help="Mass of heavy scalar X in GeV")
parser.add_argument("-S", "--SMass", default=300, type=int, help="Mass of scalar S in GeV")
parser.add_argument("-d", "--decaymode", default="H2bbH1tautau", type=str, help="Decay mode")
parser.add_argument("-n", "--npoints", default=10000, type=int, help="Initial number of scan points")
parser.add_argument("-i", "--iterations", default=100, type=int, help="Maximum number of iterations")
parser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
parser.add_argument("-p", "--useprescan", default=True, type=bool, help="Use prescan")
args = vars(parser.parse_args())

# whether prescan should be used
useprescan = args["useprescan"]

# masses
mH1 = 125
mH2 = args["SMass"]
mH3 = args["XMass"]

# decay mode
decay = args["decaymode"]

# check to make sure decay mode is supported
supported = False
if decay == "H2bbH1tautau" or decay == "H2tautauH1bb" or decay == "H2H1bbtautau":
    supported = True
if decay == "H2VVH1tautau" or decay == "H2tautauH1VV" or decay == "H2H1VVtautau":
    supported = True
if not supported:
    print("Unrecognized decay",decay)
    print("Quiting...")
    quit()

# maximum allowed width
maxwidth = args["widthmax"]

# number of scan points
npoints = args["npoints"]
minpoints = 100

# number of iterations
niter = args["iterations"]

# min and max theta values
thetahSmin = -1 * math.pi / 2
thetahSmax = math.pi / 2
thetahXmin = -1 * math.pi / 2
thetahXmax = math.pi / 2
thetaSXmin = -1 * math.pi / 2
thetaSXmax = math.pi / 2

# min and max vev values
vsmin = 0.0
vsmax = 1000.0
vxmin = 0.0
vxmax = 1000.0

base = "TRSMBroken"
tempname = base + "_template.ini"

template = open(tempname,"r")
templatedata = template.read()
template.close()

prescan = home + "/output/prescan/X"+str(mH3)+"_S"+str(mH2)+"/"+base+"_prescan.tsv"

# if prescan output doesn't exist, complain and exit
if not os.path.exists(prescan):
    print("Unable to find prescan output:",prescan)
    print("Run a prescan with at least one point before trying again")
    quit()

# get list of column numbers
cols = columns.Columns(prescan)

# directory where we want to run
dir = "output/"+decay+"/X"+str(mH3)+"_S"+str(mH2)

# check if directory exists, otherwise make it
if not os.path.exists(dir):
   os.makedirs(dir)

# directory to store all of the output files
if not os.path.exists(dir + "/files"):
   os.makedirs(dir + "/files")

# go into the run directory
os.chdir(dir)

if useprescan:

    with open(prescan, "r") as f:
        num_prescan = sum(1 for _ in f)

    if num_prescan < 0.5 * npoints:
        print("Prescan doesn't have enough points to justify using.")
        print("Run a prescan with more points or rerun scan with --useprescan=False")
        quit()

    # check ranges of the prescan
    minthS, maxthS, minthX, maxthX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx = parse.getranges(prescan,cols)

    print("thetahS",f"{minthS:1.4f}",f"{maxthS:1.4f}")
    print("thetahX",f"{minthX:1.4f}",f"{maxthX:1.4f}")
    print("thetaSX",f"{mintSX:1.4f}",f"{maxtSX:1.4f}")
    print("vs",f"{minvs:1.4f}",f"{maxvs:1.4f}")
    print("vx",f"{minvx:1.4f}",f"{maxvx:1.4f}")

    # if the prescan ranges are more than 5% away from
    # the boundaries, change the boundaries to restrict
    # scan range and minimize scan points that are wasted
    tolerance = 0.05

    # thetas
    if minthS - (abs(minthS) * tolerance) > thetahSmin:
        thetahSmin = minthS
    if minthX - (abs(minthX) * tolerance) > thetahXmin:
        thetahXmin = minthX
    if mintSX - (abs(mintSX) * tolerance) > thetaSXmin:
        thetaSXmin = mintSX
    if maxthS + (abs(maxthS) * tolerance) < thetahSmax:
        thetahSmax = maxthS
    if maxthX + (abs(maxthX) * tolerance) < thetahXmax:
        thetahXmax = maxthX
    if maxtSX + (abs(maxtSX) * tolerance) < thetaSXmax:
        thetaSXmax = maxtSX

    # vevs
    if minvs - (abs(minvs) * tolerance) > vsmin:
        vsmin = minvs
    if minvx - (abs(minvx) * tolerance) > vxmin:
        vxmin = minvx
    if maxvs + (abs(maxvs) * tolerance) < vsmax:
        vsmax = maxvs
    if maxvx + (abs(maxvx) * tolerance) < vxmax:
        vxmax = maxvx

# initialize theta means
thSmean = (thetahSmax + thetahSmin) / 2
thXmean = (thetahXmax + thetahXmin) / 2
tSXmean = (thetaSXmax + thetaSXmin) / 2

# initialize theta ranges
thSrange = thetahSmax - thetahSmin
thXrange = thetahXmax - thetahXmin
tSXrange = thetaSXmax - thetaSXmin

# initialize vev means
vsmean = (vsmax + vsmin) / 2
vxmean = (vxmax + vxmin) / 2

# initialize vev ranges
vsrange = vsmax - vsmin
vxrange = vxmax - vxmin

# annealing rate
thSrate = 0.9
thXrate = 0.9
tSXrate = 0.9
vsrate = 0.9
vxrate = 0.9

# rate of reducing scan points
# keep this larger than the volumetric annealing rate!
pointrate = 0.92

# summary file
summaryname = "scansummary.txt"
summary = open(summaryname,"w")
summary.write("Iter xbmax thetahS thetahX thetaSX vs vx\n")
summary.close()

# details file
detailsname = "scandetails.txt"
details = open(detailsname,"w")
details.write("Scan details\n\n")
details.close()

# initialize max xsec times BR and index
maxxb = 0.0
index = 0

for iter in range(niter):

    # get time of iteration start
    iterstart = time.time()

    # get iteration identifier
    identifier = f"{iter:04d}"
    print(identifier)

    outname = "./files/" + base + "_" + identifier
    ininame = outname + ".ini"
    tsvname = outname + "_RAW.tsv"

    # scan point density
    density = -999

    # set theta lows and highs
    thSlow = thSmean - thSrange / 2
    thShigh = thSmean + thSrange / 2
    thXlow = thXmean - thXrange / 2
    thXhigh = thXmean + thXrange / 2
    tSXlow = tSXmean - tSXrange / 2
    tSXhigh = tSXmean + tSXrange / 2

    # set vev lows and highs
    vslow = vsmean - vsrange / 2
    vshigh = vsmean + vsrange / 2
    vxlow = vxmean - vxrange / 2
    vxhigh = vxmean + vxrange / 2

    # impose min and max theta values
    if thSlow < thetahSmin:
        thSlow = thetahSmin
    if thXlow < thetahXmin:
        thXlow = thetahXmin
    if tSXlow < thetaSXmin:
        tSXlow = thetaSXmin
    if thShigh > thetahSmax:
        thShigh = thetahSmax
    if thXhigh > thetahXmax:
        thXhigh = thetahXmax
    if tSXhigh > thetaSXmax:
        tSXhigh = thetaSXmax

    # impose min and max vev values
    if vslow < vsmin:
        vslow = vsmin
    if vxlow < vxmin:
        vxlow = vxmin
    if vshigh > vsmax:
        vshigh = vsmax
    if vxhigh > vxmax:
        vxhigh = vxmax

    if iter == 0 and useprescan:
        tsvname = prescan

        # calculate point density from prescan
        volume = (thetahSmax - thetahSmin)
        volume *= (thetahXmax - thetahXmin)
        volume *= (thetaSXmax - thetaSXmin)
        volume *= (vsmax - vsmin)
        volume *= (vxmax - vxmin)
        density = num_prescan / volume

    else:

        # calculate point density from ranges
        volume = (thShigh - thSlow)
        volume *= (thXhigh - thXlow)
        volume *= (tSXhigh - tSXlow)
        volume *= (vshigh - vslow)
        volume *= (vxhigh - vxlow)
        density = npoints / volume

        filedata = templatedata
        filedata = filedata.replace("MH1",str(mH1))
        filedata = filedata.replace("MH2",str(mH2))
        filedata = filedata.replace("MH3",str(mH3))
        filedata = filedata.replace("T1LOW",str(thSlow))
        filedata = filedata.replace("T1HIGH",str(thShigh))
        filedata = filedata.replace("T2LOW",str(thXlow))
        filedata = filedata.replace("T2HIGH",str(thXhigh))
        filedata = filedata.replace("T3LOW",str(tSXlow))
        filedata = filedata.replace("T3HIGH",str(tSXhigh))
        filedata = filedata.replace("VSLOW",str(vslow))
        filedata = filedata.replace("VSHIGH",str(vshigh))
        filedata = filedata.replace("VXLOW",str(vxlow))
        filedata = filedata.replace("VXHIGH",str(vxhigh))

        outfile = open(ininame,"w")
        outfile.write(filedata)
        outfile.close()

        process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n", str(npoints)]
        print(process)
        subprocess.run(process)

        os.rename(base + ".tsv", tsvname)

        # run width filter
        nraw, nwidth = width.filterwidths(outname,maxwidth)

        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            continue

        nwidth2, nbounds = bounds.filterbounds(outname,maxwidth)

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            continue

    # store the previous points
    thSmeanOld = thSmean
    thXmeanOld = thXmean
    tSXmeanOld = tSXmean

    vsmeanOld = vsmean
    vxmeanOld = vxmean

    # get new points
    maxxbNew, indexNew, thSmeanNew, thXmeanNew, tSXmeanNew, vsmeanNew, vxmeanNew = parse.getmaxpoint(tsvname,cols,decay)

    update = False

    if maxxbNew > maxxb:
        update = True
        maxxb = maxxbNew
        index = indexNew
        thSmean = thSmeanNew
        thXmean = thXmeanNew
        tSXmean = tSXmeanNew
        vsmean = vsmeanNew
        vxmean = vxmeanNew

    # parameter differences
    thSdiff = 9e9
    thXdiff = 9e9
    tSXdiff = 9e9

    vsdiff = 9e9
    vxdiff = 9e9

    if abs(thSmean) > 1e-3:
        thSdiff = (thSmeanOld - thSmean) / thSmean
    if abs(thXmean) > 1e-3:
        thXdiff = (thXmeanOld - thXmean) / thXmean
    if abs(tSXmean) > 1e-3:
        tSXdiff = (tSXmeanOld - tSXmean) / tSXmean

    if abs(vsmean) > 1e-3:
        vsdiff = (vsmeanOld - vsmean) / vsmean
    if abs(vxmean) > 1e-3:
        vxdiff = (vxmeanOld - vxmean) / vxmean

    """
    # print scan details to screen
    print("index = " + str(index))
    print("maxxb = " + str(maxxb))
    print("thSmean = " + str(thSmean))
    print("thXmean = " + str(thXmean))
    print("tSXmean = " + str(tSXmean))
    print("vsmean = " + str(vsmean))
    print("vxmean = " + str(vxmean))
    """

    # get iteration end time
    iterend = time.time()
    itertime = iterend - iterstart

    # write scan details to details file
    details = open(detailsname,"a")
    details.write("Iteration = " + str(identifier) + "\n")
    if iter == 0 and useprescan:
        details.write("Checking prescan output\n")
    else:
        details.write("Using " + str(npoints) + " scan points\n")
        details.write("It took " + f"{itertime:1.1f}" + " seconds\n")
        details.write(str(nwidth) + "/" + str(nraw) + " pass width cut of " + str(maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(nwidth2) + " pass bounds check\n")
        details.write("Found max xsec*BR = " + f"{Decimal(maxxbNew):.4E}" + "\n")
        details.write("Update = " + str(update) + "\n")
    details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
    details.write("Max xsec*BR = " + f"{Decimal(maxxb):.4E}" + "\n")
    details.write("thetahS: mean = " + f"{thSmean:1.4f}" + "\n")
    details.write("         diff = " + f"{thSdiff:1.3f}" + "\n")
    details.write("         range = [" + f"{thSlow:1.4f}" + "," + f"{thShigh:1.4f}" + "]\n")
    details.write("thetahX: mean = " + f"{thXmean:1.4f}" + "\n")
    details.write("         diff = " + f"{thXdiff:1.3f}" + "\n")
    details.write("         range = [" + f"{thXlow:1.4f}" + "," + f"{thXhigh:1.4f}" + "]\n")
    details.write("thetaSX: mean = " + f"{tSXmean:1.4f}" + "\n")
    details.write("         diff = " + f"{tSXdiff:1.3f}" + "\n")
    details.write("         range = [" + f"{tSXlow:1.4f}" + "," + f"{tSXhigh:1.4f}" + "]\n")
    details.write("vs: mean = " + f"{vsmean:1.4f}" + "\n")
    details.write("    diff = " + f"{vsdiff:1.3f}" + "\n")
    details.write("    range = [" + f"{vslow:1.4f}" + "," + f"{vshigh:1.4f}" + "]\n")
    details.write("vx: mean = " + f"{vxmean:1.4f}" + "\n")
    details.write("    diff = " + f"{vxdiff:1.3f}" + "\n")
    details.write("    range = [" + f"{vxlow:1.4f}" + "," + f"{vxhigh:1.4f}" + "]\n")
    details.write("\n\n")
    details.close()

    if update is True:
        # write scan results to summary file
        summary = open(summaryname,"a")
        summary.write(identifier)
        summary.write(" " + f"{Decimal(maxxb):.4E}")
        summary.write(" " + f"{thSmean:1.4f}")
        summary.write(" " + f"{thXmean:1.4f}")
        summary.write(" " + f"{tSXmean:1.4f}")
        summary.write(" " + f"{vsmean:1.4f}")
        summary.write(" " + f"{vxmean:1.4f}")
        summary.write("\n")
        summary.close()

    # step down theta ranges
    thSrange *= thSrate
    thXrange *= thXrate
    tSXrange *= tSXrate

    # step down vev ranges
    vsrange *= vsrate
    vxrange *= vxrate

    # step down npoints
    npoints = int(npoints * pointrate)

    # make sure we use the minimum number of points
    if npoints < minpoints:
        npoints = minpoints

    ##### TODO: Add functionality to concatenate all outputs into a since large output

scanend = time.time()

scantime = (scanend - scanstart)

print("Scan took",f"{scantime:1.1f}","seconds")
details = open(detailsname,"a")
details.write("\nScan took " + f"{scantime:1.1f}" + " seconds\n")
details.close()
