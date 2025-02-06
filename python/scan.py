#!/usr/bin/env python3

# standard libraries
import argparse
from copy import deepcopy
import datetime
import itertools
import logging
import os
import shutil
import time

# local modules
from prescan import prescan
from utils.config_loader import ConfigLoader
from utils.decay_utils import is_valid_decay, valid_decays
from utils.file_utils import scan_dir, recreate_dir
from utils.logging_utils import LOG_LEVELS, setup_logging, log_table
from utils.math_utils import round_sig
from utils.model import Model
from utils.params import Params
from utils.point import Point
from utils.run_metadata import run_exists, save_run_metadata
from optimizers.zoom_optimizer import ZoomOptimizer

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 model: 'Model',
                 decay: str,
                 overwrite: bool = False,
                 config_file_name: str = ""
                 ):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # store model name
        self.model = model

        # store decay information
        self.decay = decay

        # check whether decay is valid
        if not is_valid_decay(self.decay):
            raise ValueError(
                f"Unrecognized decay {self.decay}\n"
                f"Allowed decays are: {', '.join(valid_decays())}."
            )

        # use default config file name if none is provided
        if not config_file_name:
            config_file_name = f"{self.model.name}_default.yml"

        # load config file
        self.config_loader = ConfigLoader(config_file_name=config_file_name)

        # get configurations from config file
        try:
            self.num_starting_points: float = self.config_loader.get('scan', 'num_starting_points')
            self.max_prescan_points: float = self.config_loader.get('scan', 'max_prescan_points')
        except KeyError as e:
            self.logger.error(e)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

        # make instance of params
        # this automatically initializes the parameters
        self.params = Params(model=self.model,
                             decay=decay)

        # make dummy optimal point
        self.global_max = Point(model=self.model)

        # directory where we want the output to go
        self.out_dir = scan_dir(model=self.model,
                                decay=decay)

        # remove output directory if overwrite flag is set
        if overwrite:
            self.delete_run_directory()

        # create output directory structure and initialize files
        # TODO: Is this necessary to do here?
        self.initialize_dirs()

    # create output directory structure and files for scan
    def initialize_dirs(self) -> None:

        # make output directory if it doesn't already exist
        os.makedirs(self.out_dir, exist_ok=True)

        # recreate files directory along with subdirectories
        recreate_dir(path=f"{self.out_dir}/files",
                     subdirs=["details", "ini", "tsv"])

        # create summary file
        self.summary_name = self.out_dir + f"scan_summary_{self.model.name}_{self.decay}_{self.model.mass_string}.tsv"
        with open(self.summary_name, "w") as summary:
            summary.write("xbmax")
            for parameter in self.global_max.par_vals.keys():
                summary.write(f"\t{parameter}")
            summary.write("\titer\n")

        # create raw output file
        self.tsv_summary_name = self.out_dir + f"scan_tsv_summary_{self.model.name}_{self.decay}_{self.model.mass_string}.tsv"
        with open(self.tsv_summary_name, "w"):
            pass

        # create details file
        self.details_name = self.out_dir + f"files/details/prescan_details_{self.model.name}_{self.decay}_{self.model.mass_string}.txt"
        with open(self.details_name, "w") as details:
            details.write("Scan details\n\n")

    # run a prescan to constrain scan parameter ranges
    def run_prescan(self,
                    num_points: int) -> None:

        # default number of prescan points set to 10000
        num_prescan = self.max_prescan_points

        # if fewer points are requested than num_prescan, only use that many
        if num_points < self.max_prescan_points:
            num_prescan = num_points

        try:
            # call prescan
            self.prescan_parser = prescan(num_points = num_prescan,
                                          model = self.model,
                                          config_loader = self.config_loader)

        # if prescan fails, remove directory and raise an error
        except TimeoutError:

            # delete directory
            self.delete_run_directory()

            # raise error
            raise

        # info message about prescan
        self.logger.debug(f"Analyzing prescan with {self.prescan_parser.num_unfiltered_points} points")
        self.logger.debug(f"{self.prescan_parser.num_filtered_points} passed filters")

        # print header about prescan ranges to the screen
        self.logger.info("Found the following ranges from the prescan:")

        # make list of headers for parameter bounds table and empty list of rows
        headers = ["Parameter", "Bounds"]
        rows = []

        # loop over parameters
        for parameter_name in self.params.parameter_names:

            """
            if the prescan ranges are more than 1% of the max range
            away from the boundaries, change the boundaries to restrict
            scan range and minimize scan points that are wasted
            """

            # getting 1% of min and max from the model
            one_percent = (self.params.starting_max(parameter_name) - self.params.starting_min(parameter_name)) / 100

            # get min and max from prescan
            new_min = self.prescan_parser.get_min(parameter_name)
            new_max = self.prescan_parser.get_max(parameter_name)

            # check min value
            if new_min - one_percent > self.params[parameter_name].lower_bound:
                self.params[parameter_name].lower_bound = (new_min - one_percent)

            # check max value
            if new_max + one_percent < self.params[parameter_name].upper_bound:
                self.params[parameter_name].upper_bound = (new_max + one_percent)

            # add parameter name and range to rows
            rows.append([parameter_name, self.params.parameter_value(parameter_name).format_bounds()])

        # print table of parameter bounds
        log_table(logger=self.logger,
                  headers=headers,
                  rows=rows)

        # get scan density
        density = num_prescan / self.params.volume()

        # get new points
        self.global_max = self.prescan_parser.get_max_xb_point(self.decay)

        # write scan details to details file
        with open(self.details_name, "a") as details:
            details.write("Prescan\n")
            details.write("--------------------\n")
            details.write(f"Number of prescan points = {num_prescan}\n")
            details.write(f"Scan density = {density:.3E}\n")
            details.write(f"Max xsec*BR = {self.global_max.format_xb()}\n")
            details.write("--------------------\n")
            for parameter_name in self.params.parameter_names:
                details.write(f"{parameter_name}:\n")
                details.write(f"  value = {self.global_max.format_param(parameter_name)}\n")
                details.write(f"  range = {self.params.parameter_value(parameter_name).format_range()}\n")
            details.write("--------------------\n\n\n")

        # write scan results to summary file
        with open(self.summary_name, "a") as summary:
            summary.write(self.global_max.format_xb())
            for val in self.global_max.par_vals.values():
                summary.write(f"\t{round_sig(val)}")
            summary.write("\tPre\n")

        # write scan max xb tsv line to tsv summary file
        with open(self.tsv_summary_name, "a") as tsv_summary:
            tsv_summary.write(f"{self.prescan_parser.tsv_header}\n")

        self.prescan_parser.write_max_xb_line(self.tsv_summary_name)

        # TODO: Is this needed?
        # scale new low and high values
        self.params.scale_ranges(self.global_max)

        return

    # run the full scan
    def run_zoom_optimization(self,
                              num_points: int,
                              niter: int) -> None:

        # get scan start time
        scan_start = time.time()

        # if num_points isn't given, use num_starting_points
        if num_points < 0:
            num_points = self.num_starting_points

        # check if run already exists
        if run_exists(out_dir=self.out_dir,
                        num_points=num_points):
                self.logger.info(f"Skipping scan requested with {num_points} points.")
                self.logger.info(f"Use the -o option to overwrite the existing run.")
                return

        # delete directory and reinitialize
        self.delete_run_directory()
        self.initialize_dirs()

        # run prescan
        self.run_prescan(num_points = num_points)

        # move into the working directory for scans
        os.chdir(self.out_dir)

        # make a list of all zoom optimizers based on bimodal distribution tests
        all_zoom_optimizers = self.create_zoom_optimizers(num_points=num_points)

        # list of which zoom optimizers are running
        running_list = [True]

        # to keep count of which iteration the scan is on
        iter = 0

        while any(running_list):

            # check if user has added a set number of iterations
            if niter > 0 and iter >= niter:
                self.logger.info(f"Ending after {niter} iterations as requested")
                break

            # Have a way to differentiate active zoom optimizers and inactive zoom optimizers during each iteration
            # If zoom optimizers are differentiated, maybe have different loops to only scan from active zoom optimizers
            # Consider if having a separate function to check for the maximum is best

            # TODO: possibly redistribute points to all active scanners

            running_list = []

            for zoom_optimizer in all_zoom_optimizers:

                if zoom_optimizer.is_running:

                    # store a temp_max to compare against current max_xb
                    temp_max = zoom_optimizer.run(iter=iter,
                                                  global_max=self.global_max)

                    # store max_xb
                    if temp_max > self.global_max:
                        self.global_max = temp_max
                
                # keeping track of which zoom optimizers are running
                running_list.append(zoom_optimizer.is_running)

            # count iteration
            iter += 1

        # get total scan time
        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # finalize the run
        self.finalize(optimization="zoom",
                      scan_time=scan_time,
                      num_points=num_points)

        return

    # Function that creates needed zoom optimizers
    def create_zoom_optimizers(self, num_points: int) -> list['ZoomOptimizer']:

        # Dictionary that will hold the values of the parameters
        param_dict: dict[str, list[ dict[str, float] ]] = {}

        # Populate param_dict with parameter information
        for parameter_name in self.params.parameter_names:

            # Check if bimodal and get the current low and high values
            is_bimodal = self.prescan_parser.is_bimodal(param_name=parameter_name,
                                                        decay=self.decay)
            min_val = self.params[parameter_name].low
            max_val = self.params[parameter_name].high

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
            params_copy = deepcopy(self.params)  # Manipulate data locally
            param_combination_data = {}  # Dictionary to hold all combinations of values

            # Zip the names and values together, assigning the data to each parameter
            for name, parameter in zip(param_dict.keys(), param_values):
                params_copy[name].lower_bound = parameter['min']
                params_copy[name].upper_bound = parameter['max']
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
                starting_max = self.global_max,
                config_loader = self.config_loader,
                label = f'ZoomOptimizer-{i}'
            )
            all_zoom_optimizers.append(zoom_optimizer)

        # Print the number of zoom optimizers
        self.logger.info(f"Using {len(all_zoom_optimizers)} ZoomOptimizer(s)\n")

        # Return list of all zoom optimizers
        return all_zoom_optimizers

    def finalize(self,
                 optimization: str,
                 scan_time: float,
                 num_points: int = -1) -> None:
        
        # print message indicating scan is done
        self.logger.info("Done!")

        # print out scan time
        self.logger.info(f"Scan took {datetime.timedelta(seconds=int(scan_time))} (hh:mm:ss)\n")

        # write time info to details file
        with open(self.details_name, "a") as details:
            details.write(f"Scan took {datetime.timedelta(seconds=int(scan_time))} (hh:mm:ss)\n")
    
        # save metadata
        save_run_metadata(out_dir=self.out_dir,
                          optimization=optimization,
                          num_points=num_points)

    # delete run directory if it exists
    def delete_run_directory(self) -> None:
        if os.path.exists(self.out_dir):
            self.logger.debug(f"Removing existing directory {self.out_dir}")
            shutil.rmtree(self.out_dir)

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom'], help="Optimization strategy")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous scan")
    arg_parser.add_argument("-n", "--num_points", default=-1, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-i", "--iterations", default=-1, type=int, help="Maximum number of iterations")
    arg_parser.add_argument("--log-level", default="info", choices=LOG_LEVELS.keys(), help="Set the logging level")
    arg_parser.add_argument("-l", "--log", default="scan.log", help="Log file name")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})
    
    # directory where we want the output to go
    out_dir = scan_dir(model=model,
                       decay=args.decay)

    # set up logging
    setup_logging(log_file=os.path.join(out_dir, args.log),
                  level=LOG_LEVELS[args.log_level.lower()])

    # create scan object
    myScan = Scan(model = model,
                  decay = args.decay,
                  overwrite=args.overwrite
                 )

    if args.strategy == "zoom":
        print("Running zoom optimization..")
        myScan.run_zoom_optimization(num_points = args.num_points,
                                     niter = args.iterations)
    else:
        raise ValueError(f"Selected strategy {args.strategy} is not valid. Exiting...")

