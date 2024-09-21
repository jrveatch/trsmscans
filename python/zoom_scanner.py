#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import time
import datetime

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
class ZoomScanner:

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

        # get configurations from config file
        try:
            self.num_starting_points: float = self.config_loader.get('scan', 'num_starting_points')
            self.max_prescan_points: float = self.config_loader.get('scan', 'max_prescan_points')
        except KeyError as e:
            print(f"Error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

        # make instance of params
        # this automatically initializes the parameters
        self.params = Params(model_name=model_name,
                             masses=masses)

        # make dummy optimal point
        self.global_max = Point(model_name=model_name)

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
            os.makedirs(self.outdir + "/files/details")
            os.makedirs(self.outdir + "/files/ini")
            os.makedirs(self.outdir + "/files/tsv")

        # create summary file
        self.summary_name = self.outdir + "scan_summary_" + self.model_name + "_" + self.decay + "_" + str(self.masses) + ".txt"
        summary = open(self.summary_name, "w")
        summary.write("xbmax")
        for parameter in self.params.parameters().values():
            summary.write("\t" + parameter.get_fullname())
        summary.write("\titer")
        summary.write("\n")
        summary.close()

        # create raw output file
        self.tsv_summary_name = self.outdir + "scan_tsv_summary_" + self.model_name + "_" + self.decay + "_" + str(self.masses) + ".txt"
        tsv_summary = open(self.tsv_summary_name, "w")
        tsv_summary.close()

        # create details file
        self.details_name = self.outdir + "files/details/prescan_details_" + self.model_name + "_" + self.decay + "_" + str(self.masses) + ".txt"
        details = open(self.details_name, "w")
        details.write("Scan details\n\n")
        details.close()

    # run a prescan to constrain scan parameter ranges
    def run_prescan(self,
                    num_points: int,
                    use_multiprocessing: bool = False) -> None:

        # default number of prescan points set to 10000
        nprescan = self.max_prescan_points

        # if fewer points are requested than nprescan, only use that many
        if num_points < self.max_prescan_points:
            nprescan = num_points

        try:
            # call prescan
            self.prescan_parser = run_prescan(masses = self.masses,
                                              num_points = nprescan,
                                              model_name = self.model_name,
                                              config_loader = self.config_loader,
                                              use_multiprocessing = use_multiprocessing)

        # if prescan fails, remove directory and quit
        except TimeoutError:

            # delete directory
            shutil.rmtree(self.outdir)

            # quit execution
            raise

        # get the number of unfiltered prescan points available
        n_prescan_unfiltered = self.prescan_parser.get_n_unfiltered_points()

        # get the number of filtered prescan points available
        n_prescan = self.prescan_parser.get_n_points()

        # info message about prescan
        print("\nAnalyzing prescan with", n_prescan_unfiltered, "points")
        print(n_prescan, "points passed filters")

        # if the prescan ranges are more than 1% of the max range
        # away from the boundaries, change the boundaries to restrict
        # scan range and minimize scan points that are wasted

        # print header about prescan ranges to the screen
        print("Found the following ranges from the prescan:")

        # loop over parameters
        for parameter_name in self.params.parameter_names():

            # getting 1% of min and max from the model
            one_percent = (self.params.starting_max(parameter_name) - self.params.starting_min(parameter_name)) / 100

            # get min and max from prescan
            new_min = self.prescan_parser.get_min(parameter_name)
            new_max = self.prescan_parser.get_max(parameter_name)

            # check min value
            if new_min - one_percent > self.params[parameter_name].get_lower_bound():
                self.params[parameter_name].set_lower_bound(new_min - one_percent)

            # check max value
            if new_max + one_percent < self.params[parameter_name].get_upper_bound():
                self.params[parameter_name].set_upper_bound(new_max + one_percent)

            # print min and max to screen after prescan
            self.params.print_bounds(parameter_name)

        # get scan density
        density = nprescan / self.params.volume()

        # get new points
        self.global_max = self.prescan_parser.get_max_xb_point(self.decay)

        # write scan details to details file
        details = open(self.details_name, "a")
        details.write("Prescan\n")
        details.write("--------------------\n")
        details.write("Number of prescan points = " + str(nprescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + self.global_max.format_xb() + "\n")
        details.write("--------------------\n")
        for parameter_name in self.params.parameter_names():
            details.write(parameter_name + ":\n")
            details.write("  " + self.global_max.format_param(parameter_name) + "\n")
            details.write("  " + self.params.parameter(parameter_name).format_range() + "\n")
        details.write("--------------------\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(self.summary_name, "a")
        summary.write(self.global_max.format_xb())
        for name, parameter in self.params.parameters().items():
            summary.write("\t" + f"{self.global_max.get_val(name):1.{parameter.get_precision()}f}")
        summary.write("\tPre")
        summary.write("\n")
        summary.close()

        # write scan max xb tsv line to tsv summary file
        tsv_summary = open(self.tsv_summary_name, "a")
        tsv_summary.write(self.prescan_parser.get_tsv_header() + "\n")
        tsv_summary.write(self.prescan_parser.get_max_xb_line())
        tsv_summary.close()

        # TODO: Is this needed?
        # scale new low and high values
        self.params.scale_ranges(self.global_max)

        return

    # run the full scan
    def run_zoom_optimization(self,
                              num_points: int,
                              niter: int,
                              use_multiprocessing: bool = False) -> None:

        # get scan start time
        scan_start = time.time()

        # if num_points isn't given, use num_starting_points
        if num_points < 0:
            num_points = self.num_starting_points

        # run prescan
        self.run_prescan(num_points = num_points,
                         use_multiprocessing = use_multiprocessing)

        # move into the working directory for scans
        os.chdir(self.outdir)

        # make a list of all zoom optimizers based on bimodal distribution tests
        all_zoom_optimizers = self.create_zoom_optimizers(num_points=num_points)

        # target_xb = 0

        for iter in range(niter): # make controlling num of iters optionals

            # Have a way to differentiate active zoom optimizers and inactive zoom optimizers during each iteration
            # If zoom optimizers are differentiated, maybe have different loops to only scan from active zoom optimizers
            # Consider if having a separate function to check for the maximum is best

            # TODO: possibly redistribute points to all active scanners

            for zoom_optimizer in all_zoom_optimizers:
                
                # counter to stop loop if all zoom_optimizer.running == False (to allow running without niter)

                if zoom_optimizer.is_running:

                    # store a temp_max to compare against current max_xb
                    temp_max = zoom_optimizer.run(iter=iter,
                                                  global_max=self.global_max,
                                                  use_multiprocessing=use_multiprocessing) # pass global max or use __ls__ and __gt__

                    # store max_xb
                    if temp_max > self.global_max:
                        self.global_max = temp_max
            
            #if max_xb < target_xb: # move for each zoom_optimizer to check local max (temp_max) and check twice
            #    print("Max xb less than target...")
            #    print("Ending scan early")
            #    break

            #target_xb = self.global_max + (self.global_max * 0.01)

            # TODO: Add early stopping conditions

        # get total scan time
        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # print out scan time
        print("\nDone!")
        print("Scan took", str(datetime.timedelta(seconds=int(scan_time))), "(hh:mm:ss)\n")

        # write time info to details file
        details = open(self.details_name, "a")
        details.write("Scan took " + str(datetime.timedelta(seconds=int(scan_time))) + " (hh:mm:ss)")
        details.close()
        return

    # Function that creates needed zoom optimizers
    def create_zoom_optimizers(self, num_points: int) -> list['ZoomOptimizer']:

        # Dictionary that will hold the values of the parameters
        param_dict: dict[str, list[ dict[str, float] ]] = {}

        # Populate param_dict with parameter information
        for parameter_name in self.params.parameter_names():

            # Check if bimodal and get the current low and high values
            is_bimodal = self.prescan_parser.is_bimodal(param_name=parameter_name,
                                                        decay=self.decay)
            min_val = self.params[parameter_name].get_low()
            max_val = self.params[parameter_name].get_high()

            # Split the zoom optimizer if bimodal and assign proper values
            if is_bimodal:
                mid_val = (min_val + max_val) / 2.0
                param_dict[parameter_name] = [
                    {'min': min_val, 'max': mid_val},
                    {'min': mid_val, 'max': max_val}
                ]
            else:
                param_dict[parameter_name] = [{'min': min_val, 'max': max_val}]

        # List that holds parameter value combinations
        all_param_combinations: list[tuple['Params', dict[str, float]]] = []

        # Generate all parameter combinations
        for param_values in itertools.product(*param_dict.values()):  # Itertools.product serves as a way to get combinations of values
            params_copy = copy.deepcopy(self.params)  # Manipulate data locally
            param_combination_data = {}  # Dictionary to hold all combinations of values

            # Zip the names and values together, assigning the data to each parameter
            for name, parameter in zip(param_dict.keys(), param_values):
                params_copy[name].set_lower_bound(parameter['min'])
                params_copy[name].set_upper_bound(parameter['max'])
                param_combination_data[name] = parameter

            all_param_combinations.append((params_copy, param_combination_data))

        # List that holds all the zoom optimizers created
        all_zoom_optimizers: list['ZoomOptimizer'] = []

        # Distribute points to be scanned to each zoom optimizer, rounding to the nearest whole number and having at least 1 point per zoom optimizer
        points_per_scanner = max(num_points // len(all_param_combinations), 1)

        # Initialize zoom optimizers for each parameter combination
        for i, (params_copy, param_combination_data) in enumerate(all_param_combinations):

            # Distribute points among zoom optimizers
            num_scanner_points = points_per_scanner
            if i == len(all_param_combinations) - 1:  # Ensure the last zoom optimizer gets any remaining points
                num_scanner_points = num_points - (points_per_scanner * (len(all_param_combinations) - 1))

            # Create the ZoomOptimizer
            zoom_optimizer = ZoomOptimizer(
                num_points = num_scanner_points,
                params = params_copy,
                decay = self.decay,
                starting_max = self.global_max,
                config_loader = self.config_loader,
                label = f'ZoomOptimizer-{i}'
            )
            all_zoom_optimizers.append(zoom_optimizer)

        # Print the number of zoom optimizers
        print(f"\nUsing {len(all_zoom_optimizers)} ZoomOptimizer(s)")

        # Return list of all zoom optimizers
        return all_zoom_optimizers