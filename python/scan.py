
# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse

# import decimal
from decimal import Decimal

# import tools
from parse import Parse, Point
from params import Params
import filters
import runScannerS
from masses import Masses
import prescan

thetaVars = ["tHS","tHX","tSX"]
vevVars = ["vs","vx"]
varnames = thetaVars + vevVars

class Scan:

    def __init__(self,
                 masses: 'Masses',
                 decay,
                 maxwidth,
                 base="TRSMBroken"):
        
        # store masses and decay information
        self.masses = masses
        self.decay = decay

        # check whether decay is valid
        supported = isValidDecay(self.decay)
        if not supported:
            print("Unrecognized decay",self.decay)
            print("Quitting...")
            quit()

        # store maximum allowed width
        self.maxwidth = maxwidth

        # make instance of params
        # this automatically initializes the parameters
        self.params = Params(masses)

        # make dummy optimal point
        self.optPoint = Point()

        # directory where we want the output to go
        self.outdir = os.environ['SCANDIR']+decay+"/"+str(masses)+"/"

        # remove previous directory if set to overwrite
        if os.path.exists(self.outdir):
            shutil.rmtree(self.outdir)

        # make working directory
        os.makedirs(self.outdir)

        # directory to store all of the output files
        os.makedirs(self.outdir+"/files")

        # store base name
        self.base = base

        # copy template .ini into dir
        shutil.copy(os.environ['RUNDIR']+self.base+"_template.ini",self.outdir)

        # create summary file
        self.summaryname = dir+"scansummary_"+self.decay+"_"+str(self.masses)+".txt"
        summary = open(self.summaryname,"w")
        summary.write("Iter xbmax thetaHS thetaHX thetaSX vs vx\n")
        summary.close()

        # create details file
        self.detailsname = dir+"scandetails_"+self.decay+"_"+str(self.masses)+".txt"
        details = open(self.detailsname,"w")
        details.write("Scan details\n\n")
        details.close()

        return

    # run a prescan to constrain scan parameter ranges
    def runPrescan(self,
                   npoints,
                   use_multiprocessing=False):

        # location of prescan outputs
        prescantsv = os.environ['PRESCANDIR'] + "/" + str(self.masses) + "/" + self.base + "_prescan.tsv"

        # call prescan and get result
        result = prescan.runPrescan(masses=self.masses,
                                    npoints=npoints,
                                    maxwidth=self.maxwidth,
                                    base=self.base,
                                    use_multiprocessing=use_multiprocessing)
    
        # if prescan fails, remove directory and quit
        if result < 0:
        
            # inform user
            print("Removing directory",self.outdir)

            # delete directory
            shutil.rmtree(self.outdir)

            # quit execution
            quit()

        # count the number of prescan points available
        with open(prescantsv, "r") as f:
            nprescan = sum(1 for _ in f)

        # info message about prescan
        print("\nAnalyzing prescan with",nprescan,"points")

        # get parser from prescan
        scanparser = Parse(filename=prescantsv,
                           masses=self.masses,
                           decay=self.decay)

        # if the prescan ranges are more than 5% away from
        # the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted
        # TODO: figure out a more robust way to constrain min and max

        # set tolerance from boundaries
        tolerance = 0.05

        # print header about prescan ranges to the screen
        print("Found the following ranges from the prescan:")

        # loop over variables and adjust min and max values
        for var in varnames:

            # get min and max from prescan
            newMin = scanparser.getmin(var)
            newMax = scanparser.getmax(var)

            # check min value
            if newMin > self.params.min(var) + abs(self.params.min(var)) * tolerance:
                self.params.set_min(var,newMin)

            # check max value
            if newMax < self.params.max(var) - abs(self.params.max(var)) * tolerance:
                self.params.set_max(var,newMax)

            # print min and max to the screen after prescan
            if var in thetaVars:
                print(var+": ["+f"{self.params.min(var):1.4f}"+","+f"{self.params.max(var):1.4f}"+"]")
            if var in vevVars:
                print(var+": ["+f"{self.params.min(var):1.1f}"+","+f"{self.params.max(var):1.1f}"+"]")

        # get scan density
        density = nprescan / self.params.volume()

        # get new points
        self.optPoint = scanparser.getmaxpoint()

        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Prescan\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + f"{Decimal(self.optPoint.xb):.4E}" + "\n")
        for var in thetaVars:
            details.write(var+": value = " + f"{getattr(self.optPoint,var):1.4f}" + "\n")
            details.write("     range = [" + f"{self.params.low(var):1.4f}" + "," + f"{self.params.high(var):1.4f}" + "]\n")
        for var in vevVars:
            details.write(var+": value = " + f"{getattr(self.optPoint,var):1.2f}" + "\n")
            details.write("    range = [" + f"{self.params.low(var):1.1f}" + "," + f"{self.params.high(var):1.1f}" + "]\n")
        details.write("\n")
        details.close()

        # write scan results to summary file
        summary = open(self.summaryname,"a")
        summary.write("Pre")
        summary.write(" " + f"{Decimal(optPoint.xb):.4E}")
        for var in varnames:
            if var in thetaVars:
                summary.write(" " + f"{getattr(optPoint,var):1.4f}")
            if var in vevVars:
                summary.write(" " + f"{getattr(optPoint,var):1.1f}")
        summary.write("\n")
        summary.close()

        # get new theta ranges
        tHSrange = self.params.range("tHS")
        tHXrange = self.params.range("tHX")
        tSXrange = self.params.range("tSX")

        # get new vev ranges
        vsrange = self.params.range("vs")
        vxrange = self.params.range("vx")

        # set new low and high values
        # TODO: Skip getting and passing ranges back when functionality is implemented
        self.params.set_params("tHS",self.optPoint.tHS,tHSrange)
        self.params.set_params("tHX",self.optPoint.tHX,tHXrange)
        self.params.set_params("tSX",self.optPoint.tSX,tSXrange)
        self.params.set_params("vs",self.optPoint.vs,vsrange)
        self.params.set_params("vx",self.optPoint.vx,vxrange)

        return

    def runScan(self,
                npoints,
                zoom: 'Zoom',
                use_multiprocessing=False):

        # get scan start time
        scanstart = time.time()

        # run prescan
        self.runPrescan(npoints=npoints,
                        use_multiprocessing=use_multiprocessing)

        # move into the working directory for scans
        os.chdir(self.outdir)

        # TODO: Need to find a optPoint for each scanner range
        myscanner = Scanner(npoints=npoints,
                            params=self.params,
                            optPoint=self.optPoint,
                            detailsname=self.detailsname,
                            summaryname=self.summaryname,
                            zoom=zoom,
                            dir=self.outdir,
                            label="test")

        # run multiple scan iterations
        for iter in range(niter):

            # run scanner
            myscanner.run(iter,use_multiprocessing)

            ##### TODO: Add early stopping conditions

            ##### TODO: Add functionality to concatenate all outputs into a single large output

        # get total scan time
        scanend = time.time()
        scantime = (scanend - scanstart)

        # print out scan time
        print("\nDone!")
        print("Scan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)\n")

        # write time info to details file
        details = open(self.detailsname,"a")
        details.write("Scan took "+str(datetime.timedelta(seconds=int(scantime)))+" (hh:mm:ss)")
        details.close()

        return

def runScan(masses: 'Masses',
            decay,
            npoints,
            niter,
            maxwidth,
            zoom: 'Zoom',
            use_multiprocessing=False):

    # get scan start time
    scanstart = time.time()

    # check to make sure decay mode is supported
    supported = isValidDecay(decay)
    if not supported:
        print("Unrecognized decay",decay)
        print("Quitting...")
        quit()

    # make sure we use the minimum number of points
    minpoints = 100
    if npoints < minpoints:
        npoints = minpoints

    # make instance of params
    # this automatically initializes the parameters
    params = Params(masses)

    # get scan directory
    scandir = os.environ['SCANDIR']

    # directory where we want the output to go
    dir = scandir+decay+"/"+str(masses)+"/"

    # remove previous directory if set to overwrite
    if os.path.exists(dir):
        shutil.rmtree(dir)

    # make working directory
    os.makedirs(dir)

    # directory to store all of the output files
    os.makedirs(dir+"/files")

    # base name for all files
    base = "TRSMBroken"

    # name of template .ini file
    templateini = base + "_template.ini"

    # copy template .ini into dir
    shutil.copy(os.environ['RUNDIR']+templateini,dir)

    # create summary file
    summaryname = dir+"scansummary_"+decay+"_"+str(masses)+".txt"
    summary = open(summaryname,"w")
    summary.write("Iter xbmax thetaHS thetaHX thetaSX vs vx\n")
    summary.close()

    # create details file
    detailsname = dir+"scandetails_"+decay+"_"+str(masses)+".txt"
    details = open(detailsname,"w")
    details.write("Scan details\n\n")
    details.close()

    # use prescan to help constrain scan parameters
    # TODO: Factorize this out into a separate function

    # TODO: Add the ability to reapply width and bounds filters to prescan

    # location of prescan outputs
    prescandir = os.environ['PRESCANDIR']
    prescantsv = prescandir + "/" + str(masses) + "/" + base + "_prescan.tsv"

    # call prescan and get result
    result = prescan.runPrescan(masses=masses,
                                npoints=npoints,
                                maxwidth=maxwidth,
                                use_multiprocessing=use_multiprocessing)
    
    # if prescan fails, remove directory and return
    if result < 0:
        
        # inform user
        print("Removing directory",dir)

        # delete directory
        shutil.rmtree(dir)

        # return result from process
        return result

    # count the number of prescan points available
    with open(prescantsv, "r") as f:
        nprescan = sum(1 for _ in f)

    # info message about prescan
    print("\nAnalyzing prescan with",nprescan,"points")

    # get parser from prescan
    scanparser = Parse(filename=prescantsv,
                       masses=masses,
                       decay=decay)

    # if the prescan ranges are more than 5% away from
    # the boundaries, change the boundaries to restrict
    # scan range and minimize scan points that are wasted
    # TODO: figure out a more robust way to constrain min and max

    # set tolerance from boundaries
    tolerance = 0.05

    # print header about prescan ranges to the screen
    print("Found the following ranges from the prescan:")

    # loop over variables and adjust min and max values
    for var in varnames:

        # get min and max from prescan
        newMin = scanparser.getmin(var)
        newMax = scanparser.getmax(var)

        # check min value
        if newMin > params.min(var) + abs(params.min(var)) * tolerance:
            params.set_min(var,newMin)

        # check max value
        if newMax < params.max(var) - abs(params.max(var)) * tolerance:
            params.set_max(var,newMax)

        # print min and max to the screen after prescan
        if var in thetaVars:
            print(var+": ["+f"{params.min(var):1.4f}"+","+f"{params.max(var):1.4f}"+"]")
        if var in vevVars:
            print(var+": ["+f"{params.min(var):1.1f}"+","+f"{params.max(var):1.1f}"+"]")
    
    # get scan density
    density = nprescan / params.volume()
    
    # get new points
    optPoint = scanparser.getmaxpoint()

    # write scan details to details file
    details = open(detailsname,"a")
    details.write("Prescan\n")
    details.write("Number of prescan points = " + str(nprescan) + "\n")
    details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
    details.write("Max xsec*BR = " + f"{Decimal(optPoint.xb):.4E}" + "\n")
    for var in thetaVars:
        details.write(var+": value = " + f"{getattr(optPoint,var):1.4f}" + "\n")
        details.write("     range = [" + f"{params.low(var):1.4f}" + "," + f"{params.high(var):1.4f}" + "]\n")
    for var in vevVars:
        details.write(var+": value = " + f"{getattr(optPoint,var):1.2f}" + "\n")
        details.write("    range = [" + f"{params.low(var):1.1f}" + "," + f"{params.high(var):1.1f}" + "]\n")
    details.write("\n")
    details.close()

    # write scan results to summary file
    summary = open(summaryname,"a")
    summary.write("Pre")
    summary.write(" " + f"{Decimal(optPoint.xb):.4E}")
    for var in varnames:
        if var in thetaVars:
            summary.write(" " + f"{getattr(optPoint,var):1.4f}")
        if var in vevVars:
            summary.write(" " + f"{getattr(optPoint,var):1.1f}")
    summary.write("\n")
    summary.close()

    # get new theta ranges
    tHSrange = params.range("tHS")
    tHXrange = params.range("tHX")
    tSXrange = params.range("tSX")

    # get new vev ranges
    vsrange = params.range("vs")
    vxrange = params.range("vx")

    # set new low and high values
    params.set_params("tHS",optPoint.tHS,tHSrange)
    params.set_params("tHX",optPoint.tHX,tHXrange)
    params.set_params("tSX",optPoint.tSX,tSXrange)
    params.set_params("vs",optPoint.vs,vsrange)
    params.set_params("vx",optPoint.vx,vxrange)

    # move into the working directory for scans
    os.chdir(dir)

    # TODO: Need to find a optPoint for each scanner range
    myscanner = Scanner(npoints=npoints,
                        params=params,
                        optPoint=optPoint,
                        detailsname=detailsname,
                        summaryname=summaryname,
                        zoom=zoom,
                        dir=dir,
                        label="test")

    # run multiple scan iterations
    for iter in range(niter):

        # run scanner
        myscanner.run(iter,use_multiprocessing)

        ##### TODO: Add early stopping conditions

        ##### TODO: Add functionality to concatenate all outputs into a single large output

    # get total scan time
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print out scan time
    print("\nDone!")
    print("Scan took",str(datetime.timedelta(seconds=int(scantime))),"(hh:mm:ss)\n")

    # write time info to details file
    details = open(detailsname,"a")
    details.write("Scan took "+str(datetime.timedelta(seconds=int(scantime)))+" (hh:mm:ss)")
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

class Scanner:

    def __init__(self,
                 detailsname,
                 summaryname,
                 params: 'Params',
                 npoints,
                 optPoint: 'Point',
                 zoom: 'Zoom',
                 dir,
                 label="",
                 base="TRSMBroken"):

        # some basic scanner information
        self.detailsname = detailsname
        self.summaryname = summaryname
        self.params = params
        self.npoints = npoints
        self.optPoint = optPoint
        self.dir = dir
        self.label = label
        self.base = base

        # zoom rates
        self.zoom = zoom

        # set minimum number of points per iteration
        self.minpoints = 100

        # name of template .ini file
        self.templateini = self.dir + self.base + "_template.ini"

        # create parse object without a filename
        self.scanparser = Parse(masses=masses,
                                decay=decay)

        # TODO: Names of details and summary files

    def run(self,
            iter,
            use_multiprocessing=False):

        # get time of iteration start
        iterstart = time.time()

        # get iteration identifier
        identifier = f"{iter:04d}"
        if self.label:
            identifier = self.label + "_" + identifier
        print("\nIteration:",identifier)

        print("Running scanner with identifier",identifier)

        # set names of input .ini and output .tsv files
        outname = self.dir + "files/" + self.base + "_" + identifier
        ininame = outname + ".ini"
        tsvname = outname + ".tsv"

        # write new .ini file from template and parameters
        self.params.writeini(self.templateini,ininame)

        # run ScannerS
        if use_multiprocessing:
            print("Using multiprocessing")
            self.npoints = runScannerS.runParallelProcesses(ininame,self.npoints)
        else:
            print("Using single processing")
            self.npoints = runScannerS.runSingleProcess(ininame,self.npoints)

        # TODO: Figure out what to do if process returns negative value

        # calculate point density from ranges
        volume = self.params.volume()
        density = self.npoints / volume

        # apply width and bounds filters
        # this also renames the output .tsv file
        nwidth, nbounds, npass = filters.applyFilters(self.base + ".tsv",
                                                      output_file=tsvname,
                                                      maxwidth=maxwidth,
                                                      masses=self.params.masses)

        # TODO: Figure out whether these are needed and what return values to use
        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(self.detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            return

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(self.detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            return
        
        # read output tsv into parser
        self.scanparser.readFile(filename=tsvname)

        # get new point as the maximum from the current scan
        newPoint = self.scanparser.getmaxpoint()

        update = False

        # store the previous point
        optPointOld = self.optPoint

        # if new point is better than the optimal point, replace it
        if newPoint > self.optPoint:
            update = True
            self.optPoint = newPoint

        # parameter differences
        tHSdiff = 9e9
        tHXdiff = 9e9
        tSXdiff = 9e9

        vsdiff = 9e9
        vxdiff = 9e9

        # calculate difference w.r.t. previous optimal point if new point is found
        if update:
            tHSdiff = self.optPoint.diff(optPointOld,"tHS")
            tHXdiff = self.optPoint.diff(optPointOld,"tHX")
            tSXdiff = self.optPoint.diff(optPointOld,"tSX")
            vsdiff = self.optPoint.diff(optPointOld,"vs")
            vxdiff = self.optPoint.diff(optPointOld,"vx")

        # get iteration end time
        iterend = time.time()
        itertime = iterend - iterstart

        # print iteration time to screen
        #print("Iteration took",f"{itertime:1.1f}","seconds to complete")
        print("Iteration took",str(datetime.timedelta(seconds=int(itertime))),"(hh:mm:ss)")

        # get parameter ranges, lows and highs
        self.getparams()

        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("Using " + str(self.npoints) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("It took " + f"{itertime:1.1f}" + " seconds\n")
        details.write(str(nwidth) + "/" + str(self.npoints) + " pass width cut of " + str(maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(self.npoints) + " pass bounds check\n")
        details.write(str(npass) + "/" + str(self.npoints) + " pass both checks\n")
        details.write("Found new max xsec*BR = " + f"{Decimal(newPoint.xb):.4E}" + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + f"{Decimal(self.xbOpt):.4E}" + "\n")
        details.write("thetaHS: range = [" + f"{self.tHSlow:1.4f}" + "," + f"{self.tHShigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{self.tHSOpt:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tHSdiff:1.3f}" + "\n")
        details.write("thetaHX: range = [" + f"{self.tHXlow:1.4f}" + "," + f"{self.tHXhigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{self.tHXOpt:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tHXdiff:1.3f}" + "\n")
        details.write("thetaSX: range = [" + f"{self.tSXlow:1.4f}" + "," + f"{self.tSXhigh:1.4f}" + "]\n")
        if update:
            details.write("         new optimal value = " + f"{self.tSXOpt:1.4f}" + "\n")
            details.write("         rel. diff w.r.t. previous = " + f"{tSXdiff:1.3f}" + "\n")
        details.write("vs: range = [" + f"{self.vslow:1.1f}" + "," + f"{self.vshigh:1.1f}" + "]\n")
        if update:
            details.write("    new optimal value = " + f"{self.vsOpt:1.1f}" + "\n")
            details.write("    rel. diff w.r.t. previous = " + f"{vsdiff:1.3f}" + "\n")
        details.write("vx: range = [" + f"{self.vxlow:1.1f}" + "," + f"{self.vxhigh:1.1f}" + "]\n")
        if update:
            details.write("    new optimal value = " + f"{self.vxOpt:1.1f}" + "\n")
            details.write("    rel. diff w.r.t. previous = " + f"{vxdiff:1.3f}" + "\n")
        details.write("Iteration took "+str(datetime.timedelta(seconds=int(itertime)))+" (hh:mm:ss)\n")
        details.write("\n")
        details.close()

        if update is True:
            # write scan results to summary file
            summary = open(self.summaryname,"a")
            summary.write(identifier)
            summary.write(" " + f"{Decimal(self.xbOpt):.4E}")
            for var in varnames:
                if var in thetaVars:
                    summary.write(" " + f"{getattr(self.optPoint,var):1.4f}")
                if var in vevVars:
                    summary.write(" " + f"{getattr(self.optPoint,var):1.1f}")
            summary.write("\n")
            summary.close()

        # step down theta ranges
        self.tHSrange *= 1.0 - self.zoom.thetaRate
        self.tHXrange *= 1.0 - self.zoom.thetaRate
        self.tSXrange *= 1.0 - self.zoom.thetaRate

        # step down vev ranges
        self.vsrange *= 1.0 - self.zoom.vevRate
        self.vxrange *= 1.0 - self.zoom.vevRate

        # set new low and high values
        self.params.set_params("tHS",self.tHSOpt,self.tHSrange)
        self.params.set_params("tHX",self.tHXOpt,self.tHXrange)
        self.params.set_params("tSX",self.tSXOpt,self.tSXrange)
        self.params.set_params("vs",self.vsOpt,self.vsrange)
        self.params.set_params("vx",self.vxOpt,self.vxrange)

        # get new volume
        volumeNew = self.params.volume()
        volumeRatio = volumeNew/volume

        # step down npoints
        self.npoints = int(self.npoints * volumeRatio * (1 + self.zoom.densityRate))

        # make sure npoints doesn't drop below the minimum
        if self.npoints < self.minpoints:
            self.npoints = self.minpoints

        return

    def getparams(self):

        # get parameter ranges
        self.tHSrange = self.params.range("tHS")
        self.tHXrange = self.params.range("tHX")
        self.tSXrange = self.params.range("tSX")
        self.vsrange = self.params.range("vs")
        self.vxrange = self.params.range("vx")

        # get parameter low values
        self.tHSlow = self.params.low("tHS")
        self.tHXlow = self.params.low("tHX")
        self.tSXlow = self.params.low("tSX")
        self.vslow = self.params.low("vs")
        self.vxlow = self.params.low("vx")

        # get parameter high values
        self.tHShigh = self.params.high("tHS")
        self.tHXhigh = self.params.high("tHX")
        self.tSXhigh = self.params.high("tSX")
        self.vshigh = self.params.high("vs")
        self.vxhigh = self.params.high("vx")

        # get optimal values
        self.tHSOpt = self.optPoint.tHS
        self.tHXOpt = self.optPoint.tHX
        self.tSXOpt = self.optPoint.tSX
        self.vsOpt = self.optPoint.vs
        self.vxOpt = self.optPoint.vx
        self.xbOpt = self.optPoint.xb

class Zoom:

    def __init__(self,
                 theta_range_shrink_rate,
                 vev_range_shrink_rate,
                 density_growth_rate):
        
        self.thetaRate = theta_range_shrink_rate
        self.vevRate = vev_range_shrink_rate
        self.densityRate = density_growth_rate

if __name__ == "__main__":

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", required=True, type=int, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=int, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125, type=int, help="Mass of scalar H in GeV")
    argparser.add_argument("-d", "--decaymode", required=True, type=str, help="Decay mode")
    argparser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")
    argparser.add_argument("-i", "--iterations", required=True, type=int, help="Maximum number of iterations")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-t", "--theta_range_shrink", default=0.05, type=float, help="Rate at which theta range should shrink")
    argparser.add_argument("-v", "--vev_range_shrink", default=0.1, type=float, help="Rate at which vev range should shrink")
    argparser.add_argument("-g", "--densitygrowth", default=0.2, type=float, help="Rate at which point density should grow")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    args = vars(argparser.parse_args())

    # masses
    xmass = args["XMass"]
    smass = args["SMass"]
    hmass = args["HMass"]

    # create masses object
    masses = Masses(mX=xmass,mS=smass,mH=hmass)

    # decay mode
    decay = args["decaymode"]

    # maximum allowed width
    maxwidth = args["widthmax"]

    # number of scan points
    npoints = args["npoints"]

    # number of iterations
    niter = args["iterations"]

    # point density growth and parameter range shrink rates
    theta_range_shrink_rate = args['theta_range_shrink']
    vev_range_shrink_rate = args['vev_range_shrink']
    density_growth_rate = args['densitygrowth']

    zoom = Zoom(theta_range_shrink_rate=theta_range_shrink_rate,
                vev_range_shrink_rate=vev_range_shrink_rate,
                density_growth_rate=density_growth_rate)

    # whether multiprocessing should be used
    use_multiprocessing = args['multiprocessing']

    runScan(masses=masses,
            decay=decay,
            npoints=npoints,
            niter=niter,
            maxwidth=maxwidth,
            zoom=zoom,
            use_multiprocessing=use_multiprocessing)
