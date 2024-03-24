
# import various modules to help with logistics
import os
import shutil
import subprocess
import time
import datetime
import argparse

# import math
import math

# import decimal
from decimal import Decimal

# import tools
import parse
import width
import bounds
import arrays
import params

def main():

    # get scan start time
    scanstart = time.time()

    # get home directory
    home = os.getcwd()

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", default=500, type=int, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", default=300, type=int, help="Mass of scalar S in GeV")
    argparser.add_argument("-d", "--decaymode", default="H2bbH1tautau", type=str, help="Decay mode")
    argparser.add_argument("-n", "--npoints", default=10000, type=int, help="Initial number of scan points")
    argparser.add_argument("-i", "--iterations", default=100, type=int, help="Maximum number of iterations")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-p", "--useprescan", default=False, type=bool, help="Use prescan")
    args = vars(argparser.parse_args())

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
    if decay == "H2WWH1tautau" or decay == "H2tautauH1WW" or decay == "H2H1WWtautau":
        supported = True
    if decay == "H2ZZH1tautau" or decay == "H2tautauH1ZZ" or decay == "H2H1ZZtautau":
        supported = True
    if decay == "H2VVH1tautau" or decay == "H2tautauH1VV" or decay == "H2H1VVtautau":
        supported = True
    if not supported:
        print("Unrecognized decay",decay)
        print("Quitting...")
        quit()

    # maximum allowed width
    maxwidth = args["widthmax"]

    # number of scan points
    npoints = args["npoints"]
    minpoints = 100

    # number of iterations
    niter = args["iterations"]

    # make instance of params
    # this automatically initializes the parameters
    pars = params.Params(mH1,mH2,mH3)

    # create empty list of headers
    headers = []

    # base name for all files
    base = "TRSMBroken"

    # name of template .ini file
    templateini = base + "_template.ini"

    # location of prescan outputs
    prescandir = home + "/output/prescan/X" + str(mH3) + "_S" + str(mH2) + "/"
    prescanbase = prescandir + base
    prescan = prescanbase + "_prescan.tsv"

    # if prescan output doesn't exist, complain and exit
    if useprescan == True and not os.path.exists(prescan):
        print("You are attempting to use a prescan that doesn't exist.")
        print("Please run prescan.py before continuing.")
        quit()

    # directory where we want the output to go
    dir = "output/scan/"+decay+"/X"+str(mH3)+"_S"+str(mH2)+"/"

    # check if directory exists, otherwise make it
    if not os.path.exists(dir):
        os.makedirs(dir)

    # directory to store all of the output files
    if not os.path.exists(dir + "/files"):
        os.makedirs(dir + "/files")

    # copy template .ini into dir
    shutil.copy(templateini,dir)

    # go into the run directory
    os.chdir(dir)

    # create summary file
    summaryname = "scansummary.txt"
    summary = open(summaryname,"w")
    summary.write("Iter xbmax thetaHS thetaHX thetaSX vs vx\n")
    summary.close()

    # create details file
    detailsname = "scandetails.txt"
    details = open(detailsname,"w")
    details.write("Scan details\n\n")
    details.close()

    # initialize theta means
    tHSmean = pars.tHSmean()
    tHXmean = pars.tHXmean()
    tSXmean = pars.tSXmean()

    # initialize theta ranges
    tHSrange = pars.tHSrange()
    tHXrange = pars.tHXrange()
    tSXrange = pars.tSXrange()

    # initialize vev means
    vsmean = pars.vsmean()
    vxmean = pars.vxmean()

    # initialize vev ranges
    vsrange = pars.vsrange()
    vxrange = pars.vxrange()

    # annealing rate for each parameter
    tHSrate = 0.98
    tHXrate = 0.98
    tSXrate = 0.98
    vsrate = 0.98
    vxrate = 0.98

    # volumetric annealing rate
    volrate = tHSrate * tHXrate * tSXrate * vsrate * vxrate

    # rate of reducing scan points
    # keep this larger than the volumetric annealing rate!
    pointrate = 0.9
    if pointrate <= volrate:
        print("WARNING: point annealing rate is smaller than volumetric annealing rate")
        print("This will result in the point density decreasing")

    # initialize max xsec times BR
    maxxb = 0.0

    if useprescan:

        with open(prescan, "r") as f:
            nprescan = sum(1 for _ in f)

        if nprescan < 0.5 * npoints:
            print("Prescan doesn't have enough points to justify using.")
            print("Run a prescan with more points or rerun scan with --useprescan=False")
            quit()

        # get parser from prescan
        scanparser = parse.Parse(prescan)
        # TODO: remove this
        headers = scanparser.arr.getHeaders()

        # check ranges of the prescan
        mintHS, maxtHS, mintHX, maxtHX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx = scanparser.getparams()
        
        # get new points
        maxxb, tHSmean, tHXmean, tSXmean, vsmean, vxmean = scanparser.getmaxpoint(decay)

        # print the ranges to the screen
        print("\n")
        print("Found the following ranges from the prescan:")
        print("\n")
        print("thetaHS",f"{mintHS:1.4f}",f"{maxtHS:1.4f}")
        print("thetaHX",f"{mintHX:1.4f}",f"{maxtHX:1.4f}")
        print("thetaSX",f"{mintSX:1.4f}",f"{maxtSX:1.4f}")
        print("vs",f"{minvs:1.4f}",f"{maxvs:1.4f}")
        print("vx",f"{minvx:1.4f}",f"{maxvx:1.4f}")
        print("\n")

        # if the prescan ranges are more than 5% away from
        # the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted
        # TODO: figure out a more robust way to constrain min and max
 
        tolerance = 0.05

        # thetas
        if mintHS - (abs(mintHS) * tolerance) > pars.tHSmin():
            pars.set_tHSmin(mintHS)
        if mintHX - (abs(mintHX) * tolerance) > pars.tHXmin():
            pars.set_tHXmin(mintHX)
        if mintSX - (abs(mintSX) * tolerance) > pars.tSXmin():
            pars.set_tSXmin(mintSX)
        if maxtHS + (abs(maxtHS) * tolerance) < pars.tHSmax():
            pars.set_tHSmax(maxtHS)
        if maxtHX + (abs(maxtHX) * tolerance) < pars.tHXmax():
            pars.set_tHXmax(maxtHX)
        if maxtSX + (abs(maxtSX) * tolerance) < pars.tSXmax():
            pars.set_tSXmax(maxtSX)

        # vevs
        if minvs - (abs(minvs) * tolerance) > pars.vsmin():
            pars.set_vsmin(minvs)
        if minvx - (abs(minvx) * tolerance) > pars.vxmin():
            pars.set_vxmin(minvx)
        if maxvs + (abs(maxvs) * tolerance) < pars.vsmax():
            pars.set_vsmin(maxvs)
        if maxvx + (abs(maxvx) * tolerance) < pars.vxmax():
            pars.set_vxmax(maxvx)
        
        # get scan density
        volume = pars.volume()
        density = nprescan / volume

        # write scan details to details file
        details = open(detailsname,"a")
        details.write("Prescan\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + f"{Decimal(maxxb):.4E}" + "\n")
        details.write("thetaHS: mean = " + f"{tHSmean:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.tHSlow():1.4f}" + "," + f"{pars.tHShigh():1.4f}" + "]\n")
        details.write("thetaHX: mean = " + f"{tHXmean:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.tHXlow():1.4f}" + "," + f"{pars.tHXhigh():1.4f}" + "]\n")
        details.write("thetaSX: mean = " + f"{tSXmean:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.tSXlow():1.4f}" + "," + f"{pars.tSXhigh():1.4f}" + "]\n")
        details.write("vs: mean = " + f"{vsmean:1.2f}" + "\n")
        details.write("    range = [" + f"{pars.vslow():1.2f}" + "," + f"{pars.vshigh():1.2f}" + "]\n")
        details.write("vx: mean = " + f"{vxmean:1.2f}" + "\n")
        details.write("    range = [" + f"{pars.vxlow():1.2f}" + "," + f"{pars.vxhigh():1.2f}" + "]\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(summaryname,"a")
        summary.write("Pre")
        summary.write(" " + f"{Decimal(maxxb):.4E}")
        summary.write(" " + f"{tHSmean:1.4f}")
        summary.write(" " + f"{tHXmean:1.4f}")
        summary.write(" " + f"{tSXmean:1.4f}")
        summary.write(" " + f"{vsmean:1.4f}")
        summary.write(" " + f"{vxmean:1.4f}")
        summary.write("\n")
        summary.close()

    # iterate over multiple scans
    for iter in range(niter):

        # get time of iteration start
        iterstart = time.time()

        # get iteration identifier
        identifier = f"{iter:04d}"
        print(identifier)

        # set names of input .ini and output .tsv files
        outname = "./files/" + base + "_" + identifier
        ininame = outname + ".ini"
        tsvname = outname + "_RAW.tsv"

        # scan point density
        density = -999

        # set low and high values
        pars.set_tHSvals(tHSmean,tHSrange)
        pars.set_tHXvals(tHXmean,tHXrange)
        pars.set_tSXvals(tSXmean,tSXrange)
        pars.set_vsvals(vsmean,vsrange)
        pars.set_vxvals(vxmean,vxrange)

        # set theta lows and highs
        tHSlow = pars.tHSlow()
        tHShigh = pars.tHShigh()
        tHXlow = pars.tHXlow()
        tHXhigh = pars.tHXhigh()
        tSXlow = pars.tSXlow()
        tSXhigh = pars.tSXhigh()

        # set vev lows and highs
        vslow = pars.vslow()
        vshigh = pars.vshigh()
        vxlow = pars.vxlow()
        vxhigh = pars.vxhigh()

        volume = pars.volume()

        # calculate point density from ranges
        density = npoints / volume

        # write new .ini file from template and parameters
        pars.writeini(templateini,ininame)

        process = [home + "/../ScannerS/build/TRSMBroken", "--config", ininame, "scan", "-n", str(npoints)]
        print(process)
        subprocess.run(process)

        os.rename(base + ".tsv", tsvname)

        # get headers if they don't already exist
        # TODO: is there any reason to not simply make a new parser?
        # TODO: what if the headers are not the same as the prescan?
        if not headers:
            temparr = arrays.Arrays(tsvname)
            headers = temparr.getHeaders()

        # run width filter
        nraw, nwidth = width.filterwidths(outname,headers,maxwidth)

        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            continue

        nwidth2, nbounds = bounds.filterbounds(outname,headers,maxwidth)

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            continue

        # store the previous points
        tHSmeanOld = tHSmean
        tHXmeanOld = tHXmean
        tSXmeanOld = tSXmean

        vsmeanOld = vsmean
        vxmeanOld = vxmean

        # get parser with new arrays
        # TODO: check if scanparser already exists, if so, just call loadArrays
        # BUG!!!!! This should parse the tsv after bounds, not RAW
        scanparser = parse.Parse(tsvname)

        # get new points
        maxxbNew, tHSmeanNew, tHXmeanNew, tSXmeanNew, vsmeanNew, vxmeanNew = scanparser.getmaxpoint(decay)

        update = False

        if maxxbNew > maxxb:
            update = True
            maxxb = maxxbNew
            tHSmean = tHSmeanNew
            tHXmean = tHXmeanNew
            tSXmean = tSXmeanNew
            vsmean = vsmeanNew
            vxmean = vxmeanNew

        # parameter differences
        tHSdiff = 9e9
        tHXdiff = 9e9
        tSXdiff = 9e9

        vsdiff = 9e9
        vxdiff = 9e9

        if abs(tHSmean) > 1e-3:
            tHSdiff = (tHSmeanOld - tHSmean) / tHSmean
        if abs(tHXmean) > 1e-3:
            tHXdiff = (tHXmeanOld - tHXmean) / tHXmean
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
        print("tHSmean = " + str(tHSmean))
        print("tHXmean = " + str(tHXmean))
        print("tSXmean = " + str(tSXmean))
        print("vsmean = " + str(vsmean))
        print("vxmean = " + str(vxmean))
        """

        # get iteration end time
        iterend = time.time()
        itertime = iterend - iterstart

        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(detailsname,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("Using " + str(npoints) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("It took " + f"{itertime:1.1f}" + " seconds\n")
        details.write(str(nwidth) + "/" + str(nraw) + " pass width cut of " + str(maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(nwidth2) + " pass bounds check\n")
        details.write("Found max xsec*BR = " + f"{Decimal(maxxbNew):.4E}" + "\n")
        details.write("Update = " + str(update) + "\n")
        details.write("Max xsec*BR = " + f"{Decimal(maxxb):.4E}" + "\n")
        details.write("thetaHS: mean = " + f"{tHSmean:1.4f}" + "\n")
        details.write("         diff = " + f"{tHSdiff:1.3f}" + "\n")
        details.write("         range = [" + f"{tHSlow:1.4f}" + "," + f"{tHShigh:1.4f}" + "]\n")
        details.write("thetaHX: mean = " + f"{tHXmean:1.4f}" + "\n")
        details.write("         diff = " + f"{tHXdiff:1.3f}" + "\n")
        details.write("         range = [" + f"{tHXlow:1.4f}" + "," + f"{tHXhigh:1.4f}" + "]\n")
        details.write("thetaSX: mean = " + f"{tSXmean:1.4f}" + "\n")
        details.write("         diff = " + f"{tSXdiff:1.3f}" + "\n")
        details.write("         range = [" + f"{tSXlow:1.4f}" + "," + f"{tSXhigh:1.4f}" + "]\n")
        details.write("vs: mean = " + f"{vsmean:1.2f}" + "\n")
        details.write("    diff = " + f"{vsdiff:1.3f}" + "\n")
        details.write("    range = [" + f"{vslow:1.2f}" + "," + f"{vshigh:1.2f}" + "]\n")
        details.write("vx: mean = " + f"{vxmean:1.2f}" + "\n")
        details.write("    diff = " + f"{vxdiff:1.3f}" + "\n")
        details.write("    range = [" + f"{vxlow:1.2f}" + "," + f"{vxhigh:1.2f}" + "]\n")
        details.write("\n\n")
        details.close()

        if update is True:
            # write scan results to summary file
            summary = open(summaryname,"a")
            summary.write(identifier)
            summary.write(" " + f"{Decimal(maxxb):.4E}")
            summary.write(" " + f"{tHSmean:1.4f}")
            summary.write(" " + f"{tHXmean:1.4f}")
            summary.write(" " + f"{tSXmean:1.4f}")
            summary.write(" " + f"{vsmean:1.4f}")
            summary.write(" " + f"{vxmean:1.4f}")
            summary.write("\n")
            summary.close()

        # step down theta ranges
        tHSrange *= tHSrate
        tHXrange *= tHXrate
        tSXrange *= tSXrate

        # step down vev ranges
        vsrange *= vsrate
        vxrange *= vxrate

        # step down npoints
        npoints = int(npoints * pointrate)

        # make sure we use the minimum number of points
        if npoints < minpoints:
            npoints = minpoints

        ##### TODO: Add functionality to concatenate all outputs into a single large output

    scanend = time.time()

    scantime = (scanend - scanstart)

    print("Scan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")
    details = open(detailsname,"a")
    details.write("\nScan took "+str(datetime.timedelta(seconds=int(scantime)))+" (hh:mm:ss)")
    details.close()

# call main()
main()
