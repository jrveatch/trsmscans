
# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse

# import decimal
from decimal import Decimal

# import tools
import parse
import params
import filters
import runScannerS
from masses import Masses

def runScan(XMass,
            SMass,
            decay,
            npoints,
            niter,
            maxwidth,
            theta_range_shrink_rate,
            vev_range_shrink_rate,
            density_growth_rate,
            useprescan=False,
            use_multiprocessing=False):

    # get scan start time
    scanstart = time.time()

    # H mass
    HMass = 125

    # create masses object
    masses = Masses(mX=XMass,mS=SMass,mH=HMass)

    # check to make sure decay mode is supported
    supported = isValidDecay(decay)
    if not supported:
        print("Unrecognized decay",decay)
        print("Quitting...")
        quit()

    # make sure we use the minimum number of points
    minpoints = 500
    if npoints < minpoints:
        npoints = minpoints

    # make instance of params
    # this automatically initializes the parameters
    pars = params.Params(masses)

    # base name for all files
    base = "TRSMBroken"

    # name of template .ini file
    templateini = base + "_template.ini"

    # get scan directory
    scandir = os.environ['SCANDIR']

    # directory where we want the output to go
    dir = scandir+decay+"/X"+str(XMass)+"_S"+str(SMass)+"/"

    # remove previous directory if set to overwrite
    if os.path.exists(dir):
        shutil.rmtree(dir)

    # check if directory exists, if not make it
    if not os.path.exists(dir):
        os.makedirs(dir)

    # directory to store all of the output files
    if not os.path.exists(dir + "/files"):
        os.makedirs(dir + "/files")

    # copy template .ini into dir if it doesn't already exist
    if not os.path.exists(dir+templateini):
        shutil.copy(templateini,dir)

    # go into the run directory
    os.chdir(dir)

    # create summary file
    summaryname = "scansummary_"+decay+"_X"+str(XMass)+"_S"+str(SMass)+".txt"
    summary = open(summaryname,"w")
    summary.write("Iter xbmax thetaHS thetaHX thetaSX vs vx\n")
    summary.close()

    # create details file
    detailsname = "scandetails_"+decay+"_X"+str(XMass)+"_S"+str(SMass)+".txt"
    details = open(detailsname,"w")
    details.write("Scan details\n\n")
    details.close()

    # initialize theta ranges
    tHSrange = pars.range("tHS")
    tHXrange = pars.range("tHX")
    tSXrange = pars.range("tSX")

    # initialize vev ranges
    vsrange = pars.range("vs")
    vxrange = pars.range("vx")

    # annealing rate for each parameter
    tHSrate = (1.0 - theta_range_shrink_rate)
    tHXrate = (1.0 - theta_range_shrink_rate)
    tSXrate = (1.0 - theta_range_shrink_rate)
    vsrate = (1.0 - vev_range_shrink_rate)
    vxrate = (1.0 - vev_range_shrink_rate)

    # initialize optimal point
    optPoint = parse.Point()

    if useprescan:

        # TODO: Add the ability to reapply width and bounds filters to prescan

        # location of prescan outputs
        prescandir = os.environ['PRESCANDIR']
        prescan = prescandir + "/X" + str(XMass) + "_S" + str(SMass) + "/" + base + "_prescan.tsv"

        # if prescan output doesn't exist, complain and exit
        if not os.path.exists(prescan):
            print("You are attempting to use a prescan that doesn't exist.")
            print("Please run prescan.py before continuing or run without -p.")
            quit()

        # count the number of prescan points available
        with open(prescan, "r") as f:
            nprescan = sum(1 for _ in f)

        # info message about prescan
        print("\nAnalyzing prescan with",nprescan,"points")

        # if prescan doesn't have enough points, complain and exit
        if nprescan < 0.5 * npoints:
            print("Prescan doesn't have enough points to justify using.")
            print("Run a prescan with more points or rerun scan without -p")
            quit()

        # get parser from prescan
        scanparser = parse.Parse(prescan,
                                 masses,
                                 decay=decay)

        # check ranges of the prescan
        mintHS, maxtHS, mintHX, maxtHX, mintSX, maxtSX, minvs, maxvs, minvx, maxvx = scanparser.getparams()
        
        # get new points
        optPoint = scanparser.getmaxpoint()

        # print the ranges to the screen
        print("Found the following ranges from the prescan:")
        print("thetaHS: ["+f"{mintHS:1.4f}"+","+f"{maxtHS:1.4f}"+"]")
        print("thetaHX: ["+f"{mintHX:1.4f}"+","+f"{maxtHX:1.4f}"+"]")
        print("thetaSX: ["+f"{mintSX:1.4f}"+","+f"{maxtSX:1.4f}"+"]")
        print("vs: ["+f"{maxvs:1.2f}"+","+f"{maxvs:1.2f}"+"]")
        print("vx: ["+f"{minvx:1.2f}"+","+f"{maxvx:1.2f}"+"]")

        # if the prescan ranges are more than 5% away from
        # the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted
        # TODO: figure out a more robust way to constrain min and max
 
        # set tolerance from boundaries
        tolerance = 0.05

        # thetas
        if mintHS - (abs(mintHS) * tolerance) > pars.min("tHS"):
            pars.set_min("tHS",mintHS)
        if mintHX - (abs(mintHX) * tolerance) > pars.min("tHX"):
            pars.set_min("tHX",mintHX)
        if mintSX - (abs(mintSX) * tolerance) > pars.min("tSX"):
            pars.set_min("tSX",mintSX)
        if maxtHS + (abs(maxtHS) * tolerance) < pars.max("tHS"):
            pars.set_max("tHS",maxtHS)
        if maxtHX + (abs(maxtHX) * tolerance) < pars.max("tHX"):
            pars.set_max("tHX",maxtHX)
        if maxtSX + (abs(maxtSX) * tolerance) < pars.max("tSX"):
            pars.set_max("tSX",maxtSX)

        # vevs
        if minvs - (abs(minvs) * tolerance) > pars.min("vs"):
            pars.set_min("vs",minvs)
        if minvx - (abs(minvx) * tolerance) > pars.min("vx"):
            pars.set_min("vx",minvx)
        if maxvs + (abs(maxvs) * tolerance) < pars.max("vs"):
            pars.set_min("vs",maxvs)
        if maxvx + (abs(maxvx) * tolerance) < pars.max("vx"):
            pars.set_max("vx",maxvx)
        
        # get scan density
        density = nprescan / pars.volume()

        # write scan details to details file
        details = open(detailsname,"a")
        details.write("Prescan\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + f"{Decimal(optPoint.xb):.4E}" + "\n")
        details.write("thetaHS: value = " + f"{optPoint.tHS:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.low("tHS"):1.4f}" + "," + f"{pars.high("tHS"):1.4f}" + "]\n")
        details.write("thetaHX: value = " + f"{optPoint.tHX:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.low("tHX"):1.4f}" + "," + f"{pars.high("tHX"):1.4f}" + "]\n")
        details.write("thetaSX: value = " + f"{optPoint.tSX:1.4f}" + "\n")
        details.write("         range = [" + f"{pars.low("tSX"):1.4f}" + "," + f"{pars.high("tSX"):1.4f}" + "]\n")
        details.write("vs: value = " + f"{optPoint.vs:1.2f}" + "\n")
        details.write("    range = [" + f"{pars.low("vs"):1.2f}" + "," + f"{pars.high("vs"):1.2f}" + "]\n")
        details.write("vx: value = " + f"{optPoint.vx:1.2f}" + "\n")
        details.write("    range = [" + f"{pars.low("vx"):1.2f}" + "," + f"{pars.high("vx"):1.2f}" + "]\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(summaryname,"a")
        summary.write("Pre")
        summary.write(" " + f"{Decimal(optPoint.xb):.4E}")
        summary.write(" " + f"{optPoint.tHS:1.4f}")
        summary.write(" " + f"{optPoint.tHX:1.4f}")
        summary.write(" " + f"{optPoint.tSX:1.4f}")
        summary.write(" " + f"{optPoint.vs:1.4f}")
        summary.write(" " + f"{optPoint.vx:1.4f}")
        summary.write("\n")
        summary.close()

        # get new theta ranges
        tHSrange = pars.range("tHS") * tHSrate
        tHXrange = pars.range("tHX") * tHXrate
        tSXrange = pars.range("tSX") * tSXrate

        # get new vev ranges
        vsrange = pars.range("vs") * vsrate
        vxrange = pars.range("vx") * vxrate

        # set new low and high values
        pars.set_params("tHS",optPoint.tHS,tHSrange)
        pars.set_params("tHX",optPoint.tHX,tHXrange)
        pars.set_params("tSX",optPoint.tSX,tSXrange)
        pars.set_params("vs",optPoint.vs,vsrange)
        pars.set_params("vx",optPoint.vx,vxrange)

    # iterate over multiple scans
    for iter in range(niter):

        # get time of iteration start
        iterstart = time.time()

        # get iteration identifier
        identifier = f"{iter:04d}"
        print("\nIteration:",identifier)

        # set names of input .ini and output .tsv files
        outname = "./files/" + base + "_" + identifier
        ininame = outname + ".ini"
        tsvname = outname + ".tsv"

        # get theta lows and highs
        tHSlow = pars.low("tHS")
        tHShigh = pars.high("tHS")
        tHXlow = pars.low("tHX")
        tHXhigh = pars.high("tHX")
        tSXlow = pars.low("tSX")
        tSXhigh = pars.high("tSX")

        # get vev lows and highs
        vslow = pars.low("vs")
        vshigh = pars.high("vs")
        vxlow = pars.low("vx")
        vxhigh = pars.high("vx")

        # write new .ini file from template and parameters
        pars.writeini(templateini,ininame)

        # run ScannerS
        if use_multiprocessing:
            npoints = runScannerS.runParallelProcesses(ininame,npoints)
        else:
            npoints = runScannerS.runSingleProcess(ininame,npoints)

        # calculate point density from ranges
        volume = pars.volume()
        density = npoints / volume

        # if a process returns a negative result, delete directory and return result
        if npoints < 0:

            # inform user
            print("Removing directory",dir)

            # delete directory
            shutil.rmtree(dir)

            # return result from process
            return npoints

        # apply width and bounds filters
        # this also renames the output .tsv file
        nwidth, nbounds, npass = filters.applyFilters(base + ".tsv",
                                                      output_file=tsvname,
                                                      maxwidth=maxwidth,
                                                      masses=masses)

        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            continue

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            continue

        # get parser with new arrays
        scanparser = parse.Parse(filename=tsvname,
                                 masses=masses,
                                 decay=decay)

        # get new point as the maximum from the current scan
        newPoint = scanparser.getmaxpoint()

        update = False

        # store the previous point
        optPointOld = optPoint

        # if new point is better than the optimal point, replace it
        if newPoint > optPoint:
            update = True
            optPoint = newPoint

        # parameter differences
        tHSdiff = 9e9
        tHXdiff = 9e9
        tSXdiff = 9e9

        vsdiff = 9e9
        vxdiff = 9e9

        # calculate difference w.r.t. previous optimal point if new point is found
        if update:
            tHSdiff = optPoint.diff(optPointOld,"tHS")
            tHXdiff = optPoint.diff(optPointOld,"tHX")
            tSXdiff = optPoint.diff(optPointOld,"tSX")
            vsdiff = optPoint.diff(optPointOld,"vs")
            vxdiff = optPoint.diff(optPointOld,"vx")

        # get iteration end time
        iterend = time.time()
        itertime = iterend - iterstart

        # print iteration time to screen
        print("Iteration took",f"{itertime:1.1f}","seconds to complete")

        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(detailsname,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("Using " + str(npoints) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("It took " + f"{itertime:1.1f}" + " seconds\n")
        details.write(str(nwidth) + "/" + str(npoints) + " pass width cut of " + str(maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(npoints) + " pass bounds check\n")
        details.write(str(npass) + "/" + str(npoints) + " pass both checks\n")
        details.write("Found new max xsec*BR = " + f"{Decimal(newPoint.xb):.4E}" + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + f"{Decimal(optPoint.xb):.4E}" + "\n")
        details.write("thetaHS: range = [" + f"{tHSlow:1.4f}" + "," + f"{tHShigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{optPoint.tHS:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tHSdiff:1.3f}" + "\n")
        details.write("thetaHX: range = [" + f"{tHXlow:1.4f}" + "," + f"{tHXhigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{optPoint.tHX:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tHXdiff:1.3f}" + "\n")
        details.write("thetaSX: range = [" + f"{tSXlow:1.4f}" + "," + f"{tSXhigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{optPoint.tSX:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tSXdiff:1.3f}" + "\n")
        details.write("vs: range = [" + f"{vslow:1.4f}" + "," + f"{vshigh:1.4f}" + "]\n")
        if update:
            details.write("    new optimal value = " + f"{optPoint.vs:1.2f}" + "\n")
            details.write("    rel. diff w.r.t. previous = " + f"{vsdiff:1.3f}" + "\n")
        details.write("vx: range = [" + f"{vxlow:1.4f}" + "," + f"{vxhigh:1.4f}" + "]\n")
        if update:
            details.write("    new optimal value = " + f"{optPoint.vx:1.2f}" + "\n")
            details.write("    rel. diff w.r.t. previous = " + f"{vxdiff:1.3f}" + "\n")
        details.write("\n\n")
        details.close()

        if update is True:
            # write scan results to summary file
            summary = open(summaryname,"a")
            summary.write(identifier)
            summary.write(" " + f"{Decimal(optPoint.xb):.4E}")
            summary.write(" " + f"{optPoint.tHS:1.4f}")
            summary.write(" " + f"{optPoint.tHX:1.4f}")
            summary.write(" " + f"{optPoint.tSX:1.4f}")
            summary.write(" " + f"{optPoint.vs:1.4f}")
            summary.write(" " + f"{optPoint.vx:1.4f}")
            summary.write("\n")
            summary.close()

        # step down theta ranges
        tHSrange *= tHSrate
        tHXrange *= tHXrate
        tSXrange *= tSXrate

        # step down vev ranges
        vsrange *= vsrate
        vxrange *= vxrate

        # set new low and high values
        pars.set_params("tHS",optPoint.tHS,tHSrange)
        pars.set_params("tHX",optPoint.tHX,tHXrange)
        pars.set_params("tSX",optPoint.tSX,tSXrange)
        pars.set_params("vs",optPoint.vs,vsrange)
        pars.set_params("vx",optPoint.vx,vxrange)

        # get new volume
        volumeNew = pars.volume()
        volumeRatio = volumeNew/volume

        # step down npoints
        npoints = int(npoints * volumeRatio * (1 + density_growth_rate))

        # make sure npoints doesn't drop below the minimum
        if npoints < minpoints:
            npoints = minpoints

        ##### TODO: Add early stopping conditions

        ##### TODO: Add functionality to concatenate all outputs into a single large output

    # get total scan time
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print out scan time
    print("Done!")
    print("Scan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)")

    # write time info to details file
    details = open(detailsname,"a")
    details.write("\nScan took "+str(datetime.timedelta(seconds=int(scantime)))+" (hh:mm:ss)")
    details.close()

def isValidDecay(decaymode):

    # decay mode file name
    filename = os.environ['DATADIR'] + "decaymodes.txt"

    # search for decaymode in file
    with open(filename, 'r') as file:
        # loop over every line in the file
        for line in file:
            # skip blank lines
            if line.strip():
                # get first word from each line
                first_word = line.split()[0]
                if first_word == decaymode:
                    # if it is found, return True
                    return True

    # if it isn't found, return False
    return False

if __name__ == "__main__":

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", required=True, type=int, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=int, help="Mass of scalar S in GeV")
    argparser.add_argument("-d", "--decaymode", required=True, type=str, help="Decay mode")
    argparser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")
    argparser.add_argument("-i", "--iterations", required=True, type=int, help="Maximum number of iterations")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-p", "--useprescan", action="store_true", help="Use prescan")
    argparser.add_argument("-t", "--theta_range_shrink", default=0.05, type=float, help="Rate at which theta range should shrink")
    argparser.add_argument("-v", "--vev_range_shrink", default=0.1, type=float, help="Rate at which vev range should shrink")
    argparser.add_argument("-g", "--densitygrowth", default=0.2, type=float, help="Rate at which point density should grow")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    args = vars(argparser.parse_args())

    # whether prescan should be used
    useprescan = args["useprescan"]

    # masses
    xmass = args["XMass"]
    smass = args["SMass"]

    # decay mode
    decay = args["decaymode"]

    # maximum allowed width
    maxwidth = args["widthmax"]

    # number of scan points
    npoints = args["npoints"]
    minpoints = 100

    # number of iterations
    niter = args["iterations"]

    # point density growth and parameter range shrink rates
    theta_range_shrink_rate = args['theta_range_shrink']
    vev_range_shrink_rate = args['vev_range_shrink']
    density_growth_rate = args['densitygrowth']

    # whether multiprocessing should be used
    use_multiprocessing = args['multiprocessing']

    runScan(XMass=xmass,
            SMass=smass,
            decay=decay,
            npoints=npoints,
            niter=niter,
            maxwidth=maxwidth,
            theta_range_shrink_rate=theta_range_shrink_rate,
            vev_range_shrink_rate=vev_range_shrink_rate,
            density_growth_rate=density_growth_rate,
            useprescan=useprescan,
            use_multiprocessing=use_multiprocessing)
