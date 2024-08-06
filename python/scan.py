#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse
import numpy as np
import math

# import decimal
from decimal import Decimal

# import tools
from parse import Parse
from utils.point import Point
from utils.params import Params
import filters
from utils.runScannerS import runScannerS
from utils.masses import Masses
import prescan
from utils import fileutils
from utils import tsvutils

import copy
import itertools 
import glob

from typing import List

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 masses: 'Masses',
                 modelname: str,
                 decay: str,
                 maxwidth: float,
                 percentile: float,
                 overwrite: bool = False):
        
        # store model name
        self.modelname = modelname
        
        # store masses, decay, and percentile information
        self.masses = masses
        self.decay = decay
        self.percentile = percentile

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
        self.params = Params(modelname=modelname,
                             masses=masses)

        # make dummy optimal point
        self.optPoint = Point(modelname=modelname)

        # directory where we want the output to go
        self.outdir = fileutils.scan_dir(modelname=modelname,
                                         decay=decay,
                                         masses=masses)

         # remove previous directory if set to overwrite
        if os.path.exists(self.outdir) and overwrite:
            # remove directory
            shutil.rmtree(self.outdir)

        # check if directory exists, if not make it
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
            os.makedirs(self.outdir+"/files")

        # create summary file
        self.summaryname = self.outdir+"scansummary_"+self.modelname+"_"+self.decay+"_"+str(self.masses)+".txt"
        summary = open(self.summaryname,"w")
        summary.write("Iter xbmax")
        for par in self.params.parameters().values():
            summary.write(" "+par.fullname())
        summary.write("\n")
        summary.close()

        # create details file
        self.detailsname = self.outdir+"scandetails_"+self.modelname+"_"+self.decay+"_"+str(self.masses)+".txt"
        details = open(self.detailsname,"w")
        details.write("Scan details\n\n")
        details.close()

    # run a prescan to constrain scan parameter ranges
    def runPrescan(self,
                   npoints: int,
                   use_multiprocessing: bool = False) -> None:

        # default number of prescan points set to 10000
        nprescan = 10000

        # if fewer points are requested than nprescan, only use that many
        if npoints < nprescan:
            nprescan = npoints

        # location of prescan outputs
        prescantsv = fileutils.prescan_tsv(modelname=self.modelname,
                                           masses=self.masses)

        # call prescan and get result
        result = prescan.runPrescan(masses=self.masses,
                                    npoints=nprescan,
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

        # if the prescan ranges are more than 1% of the max range  
        # away from the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted

        # print header about prescan ranges to the screen
        print("Found the following ranges from the prescan:")

        # loop over parameters
        for par in self.params.parnames():

            # getting 1% of min and max from the model
            one_percent = (self.params.starting_max(par) - self.params.starting_min(par)) / 100

            # get min and max from prescan
            newMin = self.prescanparser.get_min(par)
            newMax = self.prescanparser.get_max(par)

            # check min value
            if newMin - one_percent > self.params.lower_bound(par):
                self.params.set_lower_bound(par,newMin - one_percent)

            # check max value
            if newMax + one_percent < self.params.upper_bound(par):
                self.params.set_upper_bound(par,newMax + one_percent)

            # print min and max to screen after prescan
            self.params.print_bounds(par)

        # get scan density
        density = nprescan / self.params.volume()

        # get new points
        self.optPoint = self.prescanparser.get_max_xb_point()

        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Prescan\n")
        details.write("--------------------\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + self.optPoint.format_xb() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames():
            details.write(par+":\n")
            details.write("  "+self.optPoint.format_param(par)+"\n")
            details.write("  "+self.params.parameter(par).format_range()+"\n")
        details.write("--------------------\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(self.summaryname,"a")
        summary.write("Pre")
        summary.write(" " + self.optPoint.format_xb())
        for name, par in self.params.parameters().items():
            summary.write(" " + f"{self.optPoint.get_val(name):1.{par.precision()}f}")
        summary.write("\n")
        summary.close()

        # scale new low and high values
        self.params.scale_ranges(self.optPoint)

        return

    # run the full scan
    def runScan(self,
                npoints: int,
                niter: int,
                zoom: 'Zoom',
                use_multiprocessing: bool = False) -> None:

        # get scan start time
        scanstart = time.time()

        # run prescan
        self.runPrescan(npoints=npoints,
                        use_multiprocessing=use_multiprocessing)
        
        # move into the working directory for scans
        os.chdir(self.outdir)

        all_scanners = self.create_scanners(npoints=npoints,
                                            zoom=zoom)

        for iter in range(niter):

            # Have a way to differentiate active scanners and inactive scanners during each iteration
            # If scanners are differentiated, maybe have different loops to only scan from active scanners
            # Consider if having a seperate function to check for the maximum is best

            # trial_stopping_condition() #### Figure out why function is not able to be used

            for scanner in all_scanners:

                scanner.run(iter, use_multiprocessing)

            ##### TODO: Add early stopping conditions
            
        # Initialize directory where tsv files exist
        file_directory = self.outdir + "files"

        # Combine all the tsvs depending on their iteration (multiple scanners create multiple tsvs/iteration)
        self.combine_files(file_directory)

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
    
    def trial_stopping_condition(self):

        # Use this function to distinguish between the maximums
        curr_max = 10
        return
    
    def combine_files(self, directory):

        try:
            # Ensure the directory exists
            if not os.path.exists(directory):
                os.makedirs(directory)
            
            # List all .tsv files in the input directory
            input_files = glob.glob(os.path.join(directory, "*.tsv"))

            # Sort files by filename to ensure the correct order
            input_files.sort()
            
            # Iterate over input files in the correct order
            for inputfile in input_files:
                # Extract last 4 digits from the filename
                basename = os.path.basename(inputfile)
                last_digits = basename[-8:-4]  # Assuming the pattern is '_XXXX.tsv'

                # Create output file path based on last 4 digits
                outputfile = os.path.join(directory, f"Output_{last_digits}.tsv")
                # Save contents of current input file to respective output file
                tsvutils.saveTSVOutput(inputfile, outputfile)

        # Error exceptions
        except FileNotFoundError:
            print(f"Error: A file was not found.")
        except IOError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")
    
    # Function that creates needed scanners
    def create_scanners(self,
                        npoints: int,
                        zoom: 'Zoom') -> List['Scanner']:

        # Dictionary that will hold the values of the parameters
        param_dict = {}

        # Populate param_dict with parameter information
        for par in self.params.parnames():

            #Check if bimodal and get the current low and high values
            is_bimodal = self.prescanparser.is_bimodal(par)
            min_val = self.params.low(par)
            max_val = self.params.high(par)
            
            # Split the scanner if bimodal and assign proper values
            if is_bimodal:
                mid_val = (min_val + max_val) / 2.0
                param_dict[par] = [
                    {'min': min_val, 'max': mid_val},
                    {'min': mid_val, 'max': max_val}
                ]
            else:
                param_dict[par] = [{'min': min_val, 'max': max_val}]

        # List that holds parameter value combinations
        all_param_combinations = []

        # Generate all parameter combinations
        for param_values in itertools.product(*param_dict.values()): # Itertools.product serves as a way to get combinations of values
            params_copy = copy.deepcopy(self.params) # Manipulate data locally
            param_combination_data = {} # Dictionary to hold all combinations of values

            # Zip the names and values together, assigning the data to each parameter
            for par, values in zip(param_dict.keys(), param_values):
                params_copy.set_lower_bound(par, values['min'])
                params_copy.set_upper_bound(par, values['max'])
                param_combination_data[par] = values

            all_param_combinations.append((params_copy, param_combination_data))

        # List that holds all the scanners created
        all_scanners: List['Scanner'] = []

        # Distribute points to be scanned to each scanner, rounding to the nearest whole number and having at least 1 point per scanner
        points_per_scanner = max(npoints // len(all_param_combinations), 1)

        # Initialize scanners for each parameter combination
        for i, (params_copy, param_combination_data) in enumerate(all_param_combinations):

            # Distribute points among scanners
            points = points_per_scanner
            if i == len(all_param_combinations) - 1:  # Ensure the last scanner gets any remaining points
                points = npoints - (points_per_scanner * (len(all_param_combinations) - 1))

            # Create the Scanner
            scanner = Scanner(
                npoints=points,
                params=params_copy,
                decay=self.decay,
                maxwidth=self.maxwidth,
                optPoint=self.optPoint,
                detailsname=self.detailsname,
                summaryname=self.summaryname,
                zoom=zoom,
                percentile=self.percentile,
                outdir=self.outdir,
                label=f'Configuration-{i}'
            )
            all_scanners.append(scanner)

        # Return list of all scanners
        return all_scanners

def isValidDecay(decaymode: str) -> bool:

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
                 detailsname: str,
                 summaryname: str,
                 params: 'Params',
                 decay: str,
                 maxwidth: float,
                 npoints: int,
                 optPoint: 'Point',
                 zoom: 'Zoom',
                 percentile: float,
                 outdir: str,
                 label: str = ""):

        # some basic scanner information
        self.detailsname = detailsname
        self.summaryname = summaryname
        self.params = params
        self.decay = decay
        self.maxwidth = maxwidth
        self.npoints = npoints
        self.optPoint = optPoint
        self.outdir = outdir
        self.label = label
        self.modelname = params.model_name()
        self.percentile = percentile
        self.top_percentile = {}
        self.top_percentile_xb = None

        # zoom rates
        self.zoom = zoom

        # set minimum number of points per iteration
        self.minpoints = 100

        # create parse object without a filename
        self.scanparser = Parse(masses=self.params.masses(),
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
        temptsv = self.outdir + self.modelname + ".tsv"

        # write new .ini file from template and parameters
        self.params.write_ini(ininame)

        # run ScannerS
        self.npoints = runScannerS(ininame=ininame,
                                   modelname=self.modelname,
                                   npoints=self.npoints,
                                   use_multiprocessing=use_multiprocessing)

        # TODO: Figure out what to do if process returns negative value

        # rename output .tsv file to tsvname
        shutil.move(temptsv,tsvname)

        # calculate point density from ranges
        volume = self.params.volume()
        density = self.npoints / volume

        # apply width and bounds filters
        nwidth, nbounds, npass = filters.apply_filters(filename=tsvname,
                                                       masses=self.params.masses(),
                                                       modelname=self.modelname,
                                                       maxwidth=self.maxwidth)

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
        self.scanparser.read_file(filename=tsvname)

        # get new point as the maximum from the current scan
        newPoint = self.scanparser.get_max_xb_point()

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
        details.write(str(nwidth) + "/" + str(self.npoints) + " pass width cut of " + str(self.maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(self.npoints) + " pass bounds check\n")
        details.write(str(npass) + "/" + str(self.npoints) + " pass both checks\n")
        details.write("--------------------\n")
        details.write("Found new max xsec*BR = " + newPoint.format_xb() + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + self.optPoint.format_xb() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames():
            details.write(par+":\n")
            details.write("  "+self.params.parameter(par).format_range()+"\n")
            if update:
                details.write("  new optimal "+self.optPoint.format_param(par)+"\n")
                details.write("  "+self.optPoint.format_diff(optPointOld,par)+"\n")
                details.write("  "+self.optPoint.format_diff_frac(optPointOld,par)+"\n")
        details.write("--------------------\n")
        details.write("Iteration took "+str(datetime.timedelta(seconds=int(itertime)))+" (hh:mm:ss)\n")
        details.write("\n\n")
        details.close()

        # if a new optimal point is found
        if update is True:
            # write scan results to summary file
            summary = open(self.summaryname,"a")
            summary.write(identifier)
            summary.write(" " + self.optPoint.format_xb())
            for name, par in self.params.parameters().items():
                summary.write(" " + f"{self.optPoint.get_val(name):1.{par.precision()}f}")
            summary.write("\n")
            summary.close()

        # get paramaters to use for zooming in
        paramArrays = self.scanparser.get_parameter_arrays()

        # minimum amount of points that need to be looked at before zooming in
        min_points = 10
        percentile_threshold = self.percentile

        # get an array of xb results
        xb_array = self.scanparser.get_xb()

        # if not the first iteration, add top_percentile_xb to current xb_array
        if iter != 0:
            xb_array = np.append(xb_array, self.top_percentile_xb)

        # ensure min_points are looked
        if len(xb_array) * (1.0 - percentile_threshold / 100) < min_points:
            percentile_threshold = math.floor(100 * (1.0 - min_points/len(xb_array)))

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # create a threshold to look at the top percentile of xb points
        threshold = np.percentile(xb_array, percentile_threshold)

        # get top percentile of xb
        self.top_percentile_xb = xb_array[xb_array > threshold]

        # dictionaries to update low and high in parameters
        lowdict = {}
        highdict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in paramArrays.items():
            # if not first iteration, add top_percentile to values
            if iter != 0:
                values = np.append(values, self.top_percentile[param])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > threshold]
            # set lows and highs of each parameter
            lowdict[param] = self.top_percentile[param].min()
            highdict[param] = self.top_percentile[param].max()

        # update low and high using dictionaries
        self.params.update_low_high(lowdict, highdict)

        # TODO: reinclude old scaling as an alternative
        # parameter scaling factor
        #rangeScale = 1.0 - self.zoom.parRate

        # set new low and high values
        #self.params.scale_ranges(self.optPoint,rangeScale)

        # TODO: include these two lines in old scaling alternative
        # get new volume
        #volumeNew = self.params.volume()
        #volumeRatio = volumeNew/volume

        # step down npoints
        # self.npoints = int(self.npoints * volumeRatio * (1.0 + self.zoom.densityRate))
        
        heightRatio = (xb_array.max() - threshold) / (xb_array.max() - xb_array.min())
        self.npoints = int(self.npoints * heightRatio * (1.0 + self.zoom.densityRate))

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
    argparser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    argparser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    argparser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    argparser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")
    argparser.add_argument("-i", "--iterations", required=True, type=int, help="Maximum number of iterations")
    argparser.add_argument("-w", "--maxwidth", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-r", "--parameter_rate", default=0.05, type=float, help="Rate at which parameter range should shrink")
    argparser.add_argument("-g", "--density_growth", default=0.2, type=float, help="Rate at which point density should grow")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Whether overwrite should be used")
    argparser.add_argument("-p", "--percentile", default=95, type=int, help="Percentile cut for zooming in")
    args = argparser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    # create zoom object to hold onto rates
    zoom = Zoom(parameter_rate=args.parameter_rate,
                density_growth_rate=args.density_growth)

    # creaate scan object
    myScan = Scan(masses=masses,
                  modelname=args.model,
                  decay=args.decay,
                  maxwidth=args.maxwidth,
                  percentile=args.percentile,
                  overwrite=args.overwrite)
    
    # run scan using scan object
    myScan.runScan(npoints=args.npoints,
                   niter=args.iterations,
                   zoom=zoom,
                   use_multiprocessing=args.multiprocessing)
