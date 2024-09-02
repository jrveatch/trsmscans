#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse

# import decimal
from decimal import Decimal

# import tools
from utils.point import Point
from utils.params import Params
from utils.masses import Masses
from prescan import run_prescan
from utils import fileutils
from utils.decayutils import is_valid_decay

import copy
import itertools

from zoom_optimizer import ZoomOptimizer

from utils.config_loader import ConfigLoader

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 masses: 'Masses',
                 model_name: str,
                 decay: str,
                 config_file_name: str = "",
                 overwrite: bool = False
                 ):

        # store model name
        self.model_name = model_name

        # store masses and decay information
        self.masses = masses
        self.decay = decay

        # check whether decay is valid
        supported = is_valid_decay(self.decay)
        if not supported:
            print("Unrecognized decay", self.decay)
            print("Quitting...")
            quit()

        # use default config file name if none is provided
        if not config_file_name:
            config_file_name = model_name + "_default.yml"

        # load config file
        self.config_loader = ConfigLoader(config_file_name=config_file_name)

        # make instance of params
        # this automatically initializes the parameters
        self.params = Params(model_name=model_name,
                             masses=masses)

        # make dummy optimal point
        self.optPoint = Point(model_name=model_name)

        # directory where we want the output to go
        self.outdir = fileutils.scan_dir(model_name=model_name,
                                         decay=decay,
                                         masses=masses)

        # remove previous directory if set to overwrite
        if os.path.exists(self.outdir) and overwrite:
            # remove directory
            shutil.rmtree(self.outdir)

        # check if directory exists, if not make it
        if not os.path.exists(self.outdir):
            os.makedirs(self.outdir)
            os.makedirs(self.outdir + "/files")
            os.makedirs(self.outdir + "/files/ini")
            os.makedirs(self.outdir + "/files/tsv")

        # create summary file
        self.summaryname = self.outdir + "scansummary_" + self.model_name + "_" + self.decay + "_" + str(self.masses) + ".txt"
        summary = open(self.summaryname, "w")
        summary.write("Iter xbmax")
        for par in self.params.parameters().values():
            summary.write(" " + par.fullname())
        summary.write("\n")
        summary.close()

        # create details file
        self.detailsname = self.outdir + "scandetails_" + self.model_name + "_" + self.decay + "_" + str(self.masses) + ".txt"
        details = open(self.detailsname, "w")
        details.write("Scan details\n\n")
        details.close()

    # run a prescan to constrain scan parameter ranges
    # TODO: Come up with a different name for this
    def runPrescan(self,
                   npoints: int,
                   use_multiprocessing: bool = False) -> None:

        # default number of prescan points set to 10000
        nprescan = 10000

        # if fewer points are requested than nprescan, only use that many
        if npoints < nprescan:
            nprescan = npoints

        try:
            # call prescan
            self.prescanparser = run_prescan(masses=self.masses,
                                             npoints=nprescan,
                                             model_name=self.model_name,
                                             config_loader=self.config_loader,
                                             use_multiprocessing=use_multiprocessing)

        # if prescan fails, remove directory and quit
        except TimeoutError:

            # delete directory
            shutil.rmtree(self.outdir)

            # quit execution
            raise

        # get the number of unfiltered prescan points available
        n_prescan_unfiltered = self.prescanparser.get_n_unfiltered_points()

        # get the number of filtered prescan points available
        n_prescan = self.prescanparser.get_n_points()

        # info message about prescan
        print("\nAnalyzing prescan with", n_prescan_unfiltered, "points")
        print(n_prescan, "points passed filters")

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
                self.params.set_lower_bound(par, newMin - one_percent)

            # check max value
            if newMax + one_percent < self.params.upper_bound(par):
                self.params.set_upper_bound(par, newMax + one_percent)

            # print min and max to screen after prescan
            self.params.print_bounds(par)

        # get scan density
        density = nprescan / self.params.volume()

        # get new points
        self.optPoint = self.prescanparser.get_max_xb_point(self.decay)

        # write scan details to details file
        details = open(self.detailsname, "a")
        details.write("Prescan\n")
        details.write("--------------------\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + self.optPoint.format_xb() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames():
            details.write(par + ":\n")
            details.write("  " + self.optPoint.format_param(par) + "\n")
            details.write("  " + self.params.parameter(par).format_range() + "\n")
        details.write("--------------------\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(self.summaryname, "a")
        summary.write("Pre")
        summary.write(" " + self.optPoint.format_xb())
        for name, par in self.params.parameters().items():
            summary.write(" " + f"{self.optPoint.get_val(name):1.{par.precision()}f}")
        summary.write("\n")
        summary.close()

        # TODO: Is this needed?
        # scale new low and high values
        self.params.scale_ranges(self.optPoint)

        return

    # run the full scan
    def run_zoom_optimization(self,
                              npoints: int,
                              niter: int,
                              use_multiprocessing: bool = False) -> None:

        # get scan start time
        scanstart = time.time()

        # run prescan
        self.runPrescan(npoints=npoints,
                        use_multiprocessing=use_multiprocessing)

        # move into the working directory for scans
        os.chdir(self.outdir)

        # make a list of all zoom optimizersa based on bimodal distribution tests
        all_zoom_optimizers = self.create_zoom_optimizers(npoints=npoints)

        for iter in range(niter):

            # Have a way to differentiate active zoom optimizers and inactive zoom optimizers during each iteration
            # If zoom optimizers are differentiated, maybe have different loops to only scan from active zoom optimizers
            # Consider if having a seperate function to check for the maximum is best

            for zoom_optimizer in all_zoom_optimizers:

                zoom_optimizer.run(iter, use_multiprocessing)

            # TODO: Add early stopping conditions

        # get total scan time
        scanend = time.time()
        scantime = (scanend - scanstart)

        # print out scan time
        print("\nDone!")
        print("Scan took", str(datetime.timedelta(seconds=int(scantime))), "(hh:mm:ss)\n")

        # write time info to details file
        details = open(self.detailsname, "a")
        details.write("Scan took " + str(datetime.timedelta(seconds=int(scantime))) + " (hh:mm:ss)")
        details.close()
        return

    # Function that creates needed zoom optimizers
    def create_zoom_optimizers(self, npoints: int) -> list['ZoomOptimizer']:

        # Dictionary that will hold the values of the parameters
        param_dict = {}

        # Populate param_dict with parameter information
        for par in self.params.parnames():

            # Check if bimodal and get the current low and high values
            is_bimodal = self.prescanparser.is_bimodal(param_name=par,
                                                       decay=self.decay)
            min_val = self.params.get_low(par)
            max_val = self.params.get_high(par)

            # Split the zoom optimizer if bimodal and assign proper values
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
        for param_values in itertools.product(*param_dict.values()):  # Itertools.product serves as a way to get combinations of values
            params_copy = copy.deepcopy(self.params)  # Manipulate data locally
            param_combination_data = {}  # Dictionary to hold all combinations of values

            # Zip the names and values together, assigning the data to each parameter
            for par, values in zip(param_dict.keys(), param_values):
                params_copy.set_lower_bound(par, values['min'])
                params_copy.set_upper_bound(par, values['max'])
                param_combination_data[par] = values

            all_param_combinations.append((params_copy, param_combination_data))

        # List that holds all the zoom optimizers created
        all_zoom_optimizers: list['ZoomOptimizer'] = []

        # Distribute points to be scanned to each zoom optimizer, rounding to the nearest whole number and having at least 1 point per zoom optimizer
        points_per_scanner = max(npoints // len(all_param_combinations), 1)

        # Initialize zoom optimizers for each parameter combination
        for i, (params_copy, param_combination_data) in enumerate(all_param_combinations):

            # Distribute points among zoom optimizers
            points = points_per_scanner
            if i == len(all_param_combinations) - 1:  # Ensure the last zoom optimizer gets any remaining points
                points = npoints - (points_per_scanner * (len(all_param_combinations) - 1))

            # Create the ZoomOptimizer
            zoom_optimizer = ZoomOptimizer(
                npoints=points,
                params=params_copy,
                decay=self.decay,
                optPoint=self.optPoint,
                detailsname=self.detailsname,
                summaryname=self.summaryname,
                config_loader=self.config_loader,
                label=f'Configuration-{i}'
            )
            all_zoom_optimizers.append(zoom_optimizer)

        # Return list of all zoom optimizers
        return all_zoom_optimizers

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
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Whether overwrite should be used")
    args = argparser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass, mS=args.SMass, mH=args.HMass)

    # creaate scan object
    myScan = Scan(masses=masses,
                  model_name=args.model,
                  decay=args.decay,
                  overwrite=args.overwrite
                  )

    # run scan using scan object
    myScan.run_zoom_optimization(npoints=args.npoints,
                                 niter=args.iterations,
                                 use_multiprocessing=args.multiprocessing)
