#!/usr/bin/env python3

# standard libraries
import argparse
from copy import deepcopy
import datetime
from functools import cached_property
import itertools
import logging
import os
import shutil
import time
from typing import Dict, List, Tuple
import numpy as np

# local modules
from prescan import prescan
from utils.config_loader import ConfigLoader
from utils.decay_utils import is_valid_decay, valid_decays
from utils.file_utils import scan_dir, recreate_dir
from utils.logging_utils import LOG_LEVELS, setup_logging
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point
from utils.run_metadata import run_exists, save_run_metadata
from utils.tsv_utils import sort_tsv_file, write_point_to_summary_file, initialize_summary_file
from optimizers.mean_shift_optimizer import MeanShiftOptimizer
from optimizers.zoom_optimizer import ZoomOptimizer

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 model: Model,
                 decay: str,
                 prescan_points: int = -1,
                 overwrite: bool = False,
                 config_file_name: str = ""
                 ):

        """
        Initialize a Scan instance for parameter space optimization.

        Args:
            model (Model): The physical model object containing parameter definitions.
            decay (str): The decay mode to scan (must be valid per `valid_decays()`).
            prescan_points (int, optional): Number of points to sample during the prescan phase.
                Defaults to -1, in which case the config default is used.
            overwrite (bool, optional): Whether to overwrite existing scan results.
                Defaults to False.
            config_file_name (str, optional): Path to a YAML config file. If not specified,
                a default name based on the model is used.

        Raises:
            ValueError: If an invalid decay mode is provided.
            KeyError: If required config keys are missing.
            Exception: For unexpected errors during config loading.
        """

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        self.logger.info("Creating a new scan")
        self.logger.info(f"Model: {model.name}")
        self.logger.info(f"Masses: {model.masses}")
        self.logger.info(f"Decay: {decay}\n")

        # store model and decay information
        self.model = model
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
            self.num_starting_points: int = self.config_loader.get('scan', 'num_starting_points')
            default_prescan_points: int = self.config_loader.get('scan', 'default_prescan_points')
        except Exception as e:
            self.logger.exception(e)
            raise

        # number of prescan points to run
        self.prescan_points = prescan_points
        if self.prescan_points < 0:
            self.prescan_points = default_prescan_points

        # make instance of param space
        # this automatically initializes the parameters
        self.global_param_space = ParamSpace(model=self.model,
                                             decay=self.decay)

        # make dummy optimal point
        self.global_max = Point(model=self.model)

        # store overwrite flag
        self.overwrite = overwrite

    @cached_property
    def out_dir(self) -> str:
        """Output directory name"""
        return scan_dir(model=self.model,
                        decay=self.decay)

    def initialize_output(self,
                          optimizer: str) -> None:
        """
        Initialize the output directory structure and files for the scan.

        Args:
            optimizer (str): The name of the optimizer being used.
        """

        # make output directory if it doesn't already exist
        os.makedirs(self.out_dir, exist_ok=True)

        # list of subdirectories to create
        subdirs = ["details", "ini", "tsv"]
        if optimizer == "meanshift":
            subdirs.append("walk")

        # recreate files directory along with subdirectories
        recreate_dir(path=os.path.join(self.out_dir,optimizer),
                     subdirs=subdirs)

        # create summary file
        self.summary_name = os.path.join(self.out_dir, f"summary_{optimizer}_{self.model.name}_{self.decay}_{self.model.mass_string}.tsv")
        initialize_summary_file(file_name=self.summary_name,
                                model=self.model,
                                id_header="iter")

        # create raw output file
        self.tsv_summary_name = os.path.join(self.out_dir, f"summary_{optimizer}_tsv_{self.model.name}_{self.decay}_{self.model.mass_string}.tsv")
        with open(self.tsv_summary_name, "w"):
            pass

        # create details file
        self.details_name = os.path.join(self.out_dir,optimizer,"details",f"prescan_details_{self.model.name}_{self.decay}_{self.model.mass_string}.txt")
        with open(self.details_name, "w") as details:
            details.write("Scan details\n\n")

    def run_prescan(self) -> None:
        """
        Run a prescan to constrain the scan parameter ranges.
        """

        prescan_points = self.prescan_points

        try:
            # call prescan
            self.prescan_parser = prescan(num_points = prescan_points,
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
        self.logger.debug(f"{self.prescan_parser.num_filtered_points} passed filters\n")

        # shrink param space based on the points contained by it
        self.prescan_parser.shrink_param_space_bounds(self.global_param_space)

        # print bounds table for new global parameter space
        self.logger.info("Found the following ranges from the prescan:")
        self.global_param_space.log_bounds_table()

        # get scan density
        density = prescan_points / self.global_param_space.volume()

        # get new points
        self.global_max = self.prescan_parser.get_max_xb_point(self.decay)

        # write scan details to details file
        with open(self.details_name, "a") as details:
            content = "Prescan\n"
            content += "--------------------\n"
            content += f"Number of prescan points = {prescan_points}\n"
            content += f"Scan density = {density:.3E}\n"
            content += f"Max xsec*BR = {self.global_max.format_xb()}\n"
            content += "--------------------\n"
            for parameter_name in self.global_param_space.parameter_names:
                content += f"{parameter_name}:\n"
                content += f"  value = {self.global_max.format_param(parameter_name)}\n"
                content += f"  range = {self.global_param_space.parameter_ranges[parameter_name].format_range()}\n"
            content += "--------------------\n\n"
            details.write(content)

        # write scan results to summary file
        write_point_to_summary_file(file_name=self.summary_name,
                                    point=self.global_max,
                                    identifier="Pre")

        # write scan max xb tsv line to tsv summary file
        with open(self.tsv_summary_name, "a") as tsv_summary:
            tsv_summary.write(f"{self.prescan_parser.tsv_header}\n")

        self.global_max.write_tsv_to_file(self.tsv_summary_name)

    def run_ms_optimization(self,
                            num_optimizers: int) -> None:
        """
        Run a mean shift optimization.

        Args:
            num_optimizers (int): Number of optimizers to run.
        """

        self.logger.info("Running mean shift optimization...\n")

        # get scan start time
        scan_start = time.time()

        # initialize output directories and files
        self.initialize_output("meanshift")

        # run prescan
        self.run_prescan()

        # Define helper functions (as inner functions because only for meanshift implementation)

        # Returns a list of initial positions for shifters
        def initial_positions(points: int,
                              strategy: str) -> Tuple[Point]:
            results = []

            if strategy == 'random':
                for i in range(points):
                    results.append(self.global_param_space.random_point())
            elif strategy == 'pair':
                # TODO: Temporary block for this option until it can be fixed using Point
                raise NotImplementedError("Pair strategy not implemented yet.")
                initial_point = self.global_param_space.random_point()
                lead_coeffs = [-1 if p >= 0 else 1 for p in initial_point]
                coeff: float = self.config_loader.get('meanshift', 'pair_points_coeff') or 0.005
                offsets = [param.width * coeff for param in self.global_param_space]

                results.append(initial_point)

                next_point = list(deepcopy(initial_point))

                for i in range(1, points):
                    for i in range(len(next_point)):
                        next_point[i] += lead_coeffs[i] * offsets[i]

                    results.append(tuple(deepcopy(next_point)))

            return tuple(results)

        # Load config
        try:
            points_gen: str = self.config_loader.get('meanshift', 'points_gen')
        except Exception as e:
            self.logger.exception(e)
            raise

        initial_pos_set = initial_positions(num_optimizers, points_gen)

        self.logger.debug("Initial points:\n" + "\n".join(f"\t{p}" for p in initial_pos_set) + "\n")

        for i, initial_pos in enumerate(initial_pos_set):
            label = f"MeanShiftOptimizer-{i}"

            MeanShiftOptimizer(
                label=label,
                initial_pos=initial_pos,
                global_param_space=self.global_param_space,
                config_loader=self.config_loader
            ).run()

        # SCAN LOGIC END HERE

        # sort summary file
        # TODO: make sure to sort the tsv summary file as well
        sort_tsv_file(self.summary_name)

        # get total scan time
        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # finalize the run
        self.finalize(optimization="meanshift",
                      scan_time=scan_time)

    def run_zoom_optimization(self,
                              num_points: int,
                              niter: int) -> None:
        """
        Run a zoom optimization.

        Args:
            num_points (int): Number of points to use in the first iteration.
            niter (int): Number of iterations to run. Leave as -1 to run until natural ending criteria are met.
        """

        self.logger.info("Running zoom optimization...\n")

        # get scan start time
        scan_start = time.time()

        # if num_points isn't given, use num_starting_points
        if num_points < 0:
            num_points = self.num_starting_points

        # exit if run already exists and overwrite is not set
        if run_exists(out_dir=self.out_dir,
                      optimization="zoom",
                      num_points=num_points) and not self.overwrite:
                self.logger.info(f"Skipping scan requested with {num_points} points.")
                self.logger.info("Use the -o option to overwrite the existing run.\n")
                return

        # initialize output directories and files
        self.initialize_output("zoom")

        # run prescan
        self.run_prescan()

        # make a list of all zoom optimizers based on bimodal distribution tests
        all_zoom_optimizers = self.create_zoom_optimizers(self.global_param_space, num_points)
        #all_zoom_optimizers = self.prev_create_zoom_optimizers(num_points)

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
                    self.global_max = max(self.global_max, temp_max)

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

    def prev_create_zoom_optimizers(self, num_points: int) -> List[ZoomOptimizer]:
        """
        Create list of zoom optimizers based on the parameter space.

        Args:
            num_points (int): Number of points to use in the first iteration.
        """

        self.logger.info("USING OLD CREATE ZOOM OPTIMIZERS METHOD")

        # Dictionary that will hold the values of the parameters
        param_dict: Dict[str, List[ Dict[str, float] ]] = {}

        # Populate param_dict with parameter information
        for parameter_name in self.global_param_space.parameter_names:

            # Check if bimodal and get the current low and high values
            is_bimodal = self.prescan_parser.is_bimodal(param_name=parameter_name,
                                                        decay=self.decay)
            min_val = self.global_param_space[parameter_name].low
            max_val = self.global_param_space[parameter_name].high

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
        all_param_combinations: List[Tuple[ParamSpace, Dict[str, float]]] = []

        # Generate all parameter combinations
        for param_values in itertools.product(*param_dict.values()):  # Itertools.product serves as a way to get combinations of values
            params_copy = deepcopy(self.global_param_space)  # Manipulate data locally
            param_combination_data = {}  # Dictionary to hold all combinations of values

            # Zip the names and values together, assigning the data to each parameter
            for name, parameter in zip(param_dict.keys(), param_values):
                params_copy[name].min_value = parameter['min']
                params_copy[name].max_value = parameter['max']
                param_combination_data[name] = parameter

            all_param_combinations.append((params_copy, param_combination_data))

        # List that holds all the zoom optimizers created
        all_zoom_optimizers: List['ZoomOptimizer'] = []

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
                param_space = params_copy,
                starting_max = self.global_max,
                config_loader = self.config_loader,
                label = f'ZoomOptimizer-{i}'
            )
            all_zoom_optimizers.append(zoom_optimizer)

        # Print the number of zoom optimizers
        self.logger.info(f"Using {len(all_zoom_optimizers)} ZoomOptimizer(s)\n")

        # Return list of all zoom optimizers
        return all_zoom_optimizers
    
    def get_param_spaces(self, param_space: 'ParamSpace') -> List[ParamSpace]:

        # Intialize Lists to hold the current param spaces and the final param spaces
        current_param_space_list = [param_space]
        final_param_space_list =[]

        # Iterate through the current unchecked param spaces
        while current_param_space_list:

            # Remove the first param space and hold on to it as the current param space
            current = current_param_space_list.pop(0)

            # Iterate through the current param space
            for parameter_name in current.parameter_names:

                # Check modality by evaluating where to split
                all_splits = self.prescan_parser.get_param_space_splits(param_name=parameter_name, decay=self.decay, param_space=current)

                # Check if points to split where found
                if all_splits:

                    # Retrieve new param spaces based on the split at given points
                    new_param_spaces = current.split_range(param_name=parameter_name, split_values=all_splits)

                    # Add the new param spaces to the recurring list of param spaces
                    current_param_space_list.extend(new_param_spaces)
            
                    break

            # Append the current list if no further splitting was done to current param space
            else:
                final_param_space_list.append(current)

        # Shrink the param spaces in final_param_space_list
        for space in final_param_space_list:

            # Shrink the param space
            self.prescan_parser.shrink_param_space_bounds(param_space=space)
        
        return final_param_space_list

    def create_zoom_optimizers(self, param_space: ParamSpace, num_points: int) -> List[ZoomOptimizer]:

        """
        Create list of zoom optimizers based on the parameter space.

        Args:
            param_space (ParamSpace): Global parameter space
            num_points (int): Number of points to use in the first iteration.
        """

        self.logger.info("USING NEW CREATE ZOOM OPTIMIZERS METHOD")

        # Retrieve the list of param spaces
        list_of_param_spaces = self.get_param_spaces(param_space)

        # List that holds all the zoom optimizers created
        all_zoom_optimizers: List['ZoomOptimizer'] = []

        points_per_optimizer_list = self.distribute_points(list_of_param_spaces, num_points)

        # Create zoom optimizers based on param spaces
        for i, space in enumerate(list_of_param_spaces):
            zoom_optimizer = ZoomOptimizer(
                num_points = points_per_optimizer_list[i],
                param_space = space,
                starting_max = self.global_max,
                config_loader = self.config_loader,
                label = f'ZoomOptimizer-{i}'
            )

            self.logger.info(f"Number of points for optimizer {i}: {points_per_optimizer_list[i]}")

            # Append zoom optimizers to all_zoom_optimizers list
            all_zoom_optimizers.append(zoom_optimizer)

        # Print the number of zoom optimizers
        self.logger.info(f"Using {len(all_zoom_optimizers)} ZoomOptimizer(s)\n")
        
        # Return list of all zoom optimizers
        return all_zoom_optimizers

    def distribute_points(self, param_space_list: List[ParamSpace], num_points: int) -> Tuple[int]:

        # Retrieve number of param spaces
        num_param_spaces = len(param_space_list)

        # Initialize list of param space volumes
        volumes = np.array([space.volume() for space in param_space_list])

        # Retrieve total volume of all param spaces
        total_volume = volumes.sum()

        # Calculate volume by points & how many points each zoom optimizer scans
        points_per_vol_array = (volumes / total_volume) * num_points

        # Round the number of points needed for the scan
        points_array = np.round(points_per_vol_array, decimals=0, out=None).astype(int)

        # Assign rounded points to the points_per_optimizer_array
        points_per_optimizer_array = points_array

        # Minimum points assigment
        min_points = min(num_points/10,20)
        self.logger.debug(f"Minimum points per zoom optimizer: {min_points}")

        # Distribute remaining points to indices by param space volume size
        for i in range(num_param_spaces):
    
            if points_array[i] < min_points:
                points_per_optimizer_array[i] = min_points
            
        # Return to call
        return tuple(points_per_optimizer_array.tolist())
       
    def finalize(self,
                 optimization: str,
                 scan_time: float,
                 num_points: int = -1) -> None:
        """
        Finalize the scan by saving metadata and cleaning up.

        Args:
            optimization (str): The optimization method used.
            scan_time (float): The total time taken for the scan.
            num_points (int, optional): Number of points to use in the first iteration. Defaults to -1.
        """

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

    def delete_run_directory(self) -> None:
        """
        Delete the run directory if it exists.
        """
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
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous scan")
    arg_parser.add_argument("-p", "--prescan_points", default=-1, type=int, help="Number of prescan points")
    arg_parser.add_argument("-n", "--num_points", default=-1, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-i", "--iterations", default=-1, type=int, help="Maximum number of iterations/optimizers")
    arg_parser.add_argument("--log-level", default="info", choices=LOG_LEVELS.keys(), help="Set the logging level")
    arg_parser.add_argument("-l", "--log", default="", help="Log file name")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    # directory where we want the output to go
    out_dir = scan_dir(model=model,
                       decay=args.decay)

    # set up logging
    logfile_name = args.log if args.log else f"{args.strategy}.log"
    setup_logging(log_file=os.path.join(out_dir, logfile_name),
                  level=LOG_LEVELS[args.log_level.lower()])

    # create scan object
    myScan = Scan(model = model,
                  decay = args.decay,
                  prescan_points = args.prescan_points,
                  overwrite=args.overwrite
                 )

    if args.strategy == "zoom":
        myScan.run_zoom_optimization(num_points = args.num_points,
                                     niter = args.iterations)
    elif args.strategy == "meanshift":
        myScan.run_ms_optimization(num_optimizers=args.iterations)
    else:
        raise ValueError(f"Selected strategy {args.strategy} is not valid. Exiting...")
