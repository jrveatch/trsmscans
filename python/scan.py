
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

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 masses: 'Masses',
                 decay,
                 maxwidth,
                 modelname="TRSMBroken"):

        # store model name
        self.modelname = modelname
        
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
        self.params = Params(modelname,masses)

        # make dummy optimal point
        self.optPoint = Point(modelname=modelname)

        # directory where we want the output to go
        self.outdir = os.environ['SCANDIR']+decay+"/"+str(masses)+"/"

        # remove previous directory if set to overwrite
        if os.path.exists(self.outdir):
            shutil.rmtree(self.outdir)

        # make working directory
        os.makedirs(self.outdir)

        # directory to store all of the output files
        os.makedirs(self.outdir+"/files")

        # create summary file
        self.summaryname = self.outdir+"scansummary_"+self.modelname+"_"+self.decay+"_"+str(self.masses)+".txt"
        summary = open(self.summaryname,"w")
        summary.write("Iter xbmax")
        for par in self.params.parameters.values():
            summary.write(" "+par.fullname)
        summary.write("\n")
        summary.close()

        # create details file
        self.detailsname = self.outdir+"scandetails_"+self.modelname+"_"+self.decay+"_"+str(self.masses)+".txt"
        details = open(self.detailsname,"w")
        details.write("Scan details\n\n")
        details.close()

        return

    # run a prescan to constrain scan parameter ranges
    def runPrescan(self,
                   npoints,
                   use_multiprocessing=False):

        # location of prescan outputs
        prescantsv = os.environ['PRESCANDIR'] + "/" + str(self.masses) + "/" + self.modelname + "_prescan.tsv"

        # call prescan and get result
        result = prescan.runPrescan(masses=self.masses,
                                    npoints=npoints,
                                    maxwidth=self.maxwidth,
                                    modelname=self.modelname,
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
        self.prescanparser = Parse(filename=prescantsv,
                                   masses=self.masses,
                                   modelname=self.modelname,
                                   decay=self.decay)

        # if the prescan ranges are more than 5% away from
        # the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted
        # TODO: figure out a more robust way to constrain min and max

        # set tolerance from boundaries
        tolerance = 0.05

        # print header about prescan ranges to the screen
        print("Found the following ranges from the prescan:")

        # loop over parameters
        for par in self.params.parnames:

            # get min and max from prescan
            newMin = self.prescanparser.getmin(par)
            newMax = self.prescanparser.getmax(par)

            # check min value
            if newMin > self.params.min(par) + abs(self.params.min(par)) * tolerance:
                self.params.setMin(par,newMin)

            # check max value
            if newMax < self.params.max(par) - abs(self.params.max(par)) * tolerance:
                self.params.setMax(par,newMax)

            # print min and max to screen after prescan
            self.params.printMinMax(par)

        # get scan density
        density = nprescan / self.params.volume()

        # get new points
        self.optPoint = self.prescanparser.getmaxpoint()

        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Prescan\n")
        details.write("--------------------\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + self.optPoint.formatXB() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames:
            details.write(par+":\n")
            details.write("  "+self.optPoint.formatParam(par)+"\n")
            details.write("  "+self.params.parameters[par].formatRange()+"\n")
        details.write("--------------------\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(self.summaryname,"a")
        summary.write("Pre")
        summary.write(" " + self.optPoint.formatXB())
        for name, par in self.params.parameters.items():
            summary.write(" " + f"{self.optPoint.getVal(name):1.{par.precision}f}")
        summary.write("\n")
        summary.close()

        # set new low and high values
        self.params.updateParams(self.optPoint)

        return

    # run the full scan
    def runScan(self,
                npoints,
                niter,
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
                            decay=self.decay,
                            optPoint=self.optPoint,
                            detailsname=self.detailsname,
                            summaryname=self.summaryname,
                            zoom=zoom,
                            outdir=self.outdir,
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

# class that keeps track of a single scan procedure
class Scanner:

    def __init__(self,
                 detailsname,
                 summaryname,
                 params: 'Params',
                 decay,
                 npoints,
                 optPoint: 'Point',
                 zoom: 'Zoom',
                 outdir,
                 label=""):

        # some basic scanner information
        self.detailsname = detailsname
        self.summaryname = summaryname
        self.params = params
        self.decay = decay
        self.npoints = npoints
        self.optPoint = optPoint
        self.outdir = outdir
        self.label = label
        self.modelname = params.model.name

        # zoom rates
        self.zoom = zoom

        # set minimum number of points per iteration
        self.minpoints = 100

        # create parse object without a filename
        self.scanparser = Parse(masses=self.params.masses,
                                modelname=self.modelname,
                                decay=self.decay)

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

        # set names of input .ini and output .tsv files
        outname = self.outdir + "files/" + self.modelname + "_" + identifier
        ininame = outname + ".ini"
        tsvname = outname + ".tsv"

        # write new .ini file from template and parameters
        self.params.writeini(ininame)

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
        # TODO: This will probably be model dependent
        nwidth, nbounds, npass = filters.applyFilters(self.modelname + ".tsv",
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

        # flag to indicate whether optimal point needs to be updated
        update = False

        # store the previous point
        optPointOld = self.optPoint

        # if new point is better than the optimal point, replace it
        if newPoint > self.optPoint:
            update = True
            self.optPoint = newPoint

        # get iteration end time
        iterend = time.time()
        itertime = iterend - iterstart

        # print iteration time to screen
        print("Iteration took",str(datetime.timedelta(seconds=int(itertime))),"(hh:mm:ss)")

        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("--------------------\n")
        details.write("Using " + str(self.npoints) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("It took " + f"{itertime:1.1f}" + " seconds\n")
        details.write(str(nwidth) + "/" + str(self.npoints) + " pass width cut of " + str(maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(self.npoints) + " pass bounds check\n")
        details.write(str(npass) + "/" + str(self.npoints) + " pass both checks\n")
        details.write("--------------------\n")
        details.write("Found new max xsec*BR = " + newPoint.formatXB() + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + self.optPoint.formatXB() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames:
            details.write(par+":\n")
            details.write("  "+self.params.parameters[par].formatRange()+"\n")
            if update:
                details.write("  new optimal "+self.optPoint.formatParam(par)+"\n")
                details.write("  "+self.optPoint.formatDiff(optPointOld,par)+"\n")
                details.write("  "+self.optPoint.formatDiffFrac(optPointOld,par)+"\n")
        details.write("--------------------\n")
        details.write("Iteration took "+str(datetime.timedelta(seconds=int(itertime)))+" (hh:mm:ss)\n")
        details.write("\n\n")
        details.close()

        # if a new optimal point is found
        if update is True:
            # write scan results to summary file
            summary = open(self.summaryname,"a")
            summary.write(identifier)
            summary.write(" " + self.optPoint.formatXB())
            for name, par in self.params.parameters.items():
                summary.write(" " + f"{self.optPoint.getVal(name):1.{par.precision}f}")
            summary.write("\n")
            summary.close()

        # parameter scaling factor
        rangeScale = 1.0 - self.zoom.parRate

        # set new low and high values
        self.params.updateParams(self.optPoint,rangeScale)

        # get new volume
        volumeNew = self.params.volume()
        volumeRatio = volumeNew/volume

        # step down npoints
        self.npoints = int(self.npoints * volumeRatio * (1.0 + self.zoom.densityRate))

        # make sure npoints doesn't drop below the minimum
        if self.npoints < self.minpoints:
            self.npoints = self.minpoints

        return

# class to hold onto range decay and density growth rates
class Zoom:

    def __init__(self,
                 parameter_rate,
                 density_growth_rate):
        
        self.parRate = parameter_rate
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
    argparser.add_argument("-r", "--parameter_rate", default=0.05, type=float, help="Rate at which parameter range should shrink")
    argparser.add_argument("-g", "--density_growth", default=0.2, type=float, help="Rate at which point density should grow")
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
    parameter_rate = args['parameter_rate']
    density_growth_rate = args['density_growth']

    # zoom object to hold onto rates
    zoom = Zoom(parameter_rate=parameter_rate,
                density_growth_rate=density_growth_rate)

    # whether multiprocessing should be used
    use_multiprocessing = args['multiprocessing']

    # creaate scan object
    myScan = Scan(masses=masses,
                  decay=decay,
                  maxwidth=maxwidth)
    
    # run scan using scan object
    myScan.runScan(npoints=npoints,
                   niter=niter,
                   zoom=zoom,
                   use_multiprocessing=use_multiprocessing)
