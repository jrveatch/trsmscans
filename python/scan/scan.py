
# standard libraries
import datetime
from functools import cached_property
import os
import shutil
import time
from typing import List, Optional, Tuple
import numpy as np

# local modules
from prescan.prescan import prescan
from utils.config_loader import ConfigLoader
from utils.decay_utils import is_valid_decay, valid_decays
from utils.file_utils import scan_dir, recreate_dir
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point
from utils.point_sampler import PointSampler
from utils.precision_utils import Precision
from utils.metadata_utils import save_run_metadata
from utils.tsv_utils import sort_tsv_file, write_point_to_summary_file, initialize_summary_file
from optimizers.mean_shift_optimizer import MeanShiftOptimizer
from optimizers.zoom_optimizer import ZoomOptimizer
from optimizers.bayesian_optimizer import BayesianOptimizer

# get logger
import logging
logger = logging.getLogger(__name__)

# class to organize and run a complete scan
class Scan:

    def __init__(self,
                 model: Model,
                 decay: str,
                 precision: Optional[Precision] = None,
                 limit_target: Optional[float] = None,
                 prescan_points: Optional[int] = None
                 ):

        """
        Initialize a Scan instance for parameter space optimization.

        Args:
            model (Model): The physical model object containing parameter definitions.
            decay (str): The decay mode to scan (must be valid per `valid_decays()`).
            precision (Optional[Precision]): The precision level for the scan.
                Defaults to None.
            limit_target (Optional[float]): The target experimental limit for setting precision.
            prescan_points (Optional[int]): Number of points to sample during the prescan phase.

        Raises:
            ValueError: If an invalid decay mode is provided.
            KeyError: If required config keys are missing.
            Exception: For unexpected errors during config loading.
        """

        logger.info("Creating a new scan")
        logger.info(f"Model: {model.name}")
        logger.info(f"Masses: {model.masses}")
        logger.info(f"Decay: {decay}")
        if precision is not None:
            logger.info(f"Precision: {precision}")
        else:
            logger.info("Precision: adaptive")

        # store model and decay information
        self.model = model
        self.decay = decay

        # check whether decay is valid
        if not is_valid_decay(self.decay):
            raise ValueError(
                f"Unrecognized decay {self.decay}\n"
                f"Allowed decays are: {', '.join(valid_decays())}."
            )

        # load optimizer config file
        self.optimizer_config = ConfigLoader("OptimizerConfig.yml")

        # set precision, limit target and adaptive precision flag
        self.precision = precision
        self.limit_target = limit_target
        self.use_adaptive_precision = precision is None

        # some information about using adaptive precision
        if self.use_adaptive_precision:
            logger.info(f"Adaptive precision enabled. Limit target: {self.limit_target}")

        # number of prescan points to run
        self.prescan_points = prescan_points
        if self.prescan_points is None:
            self.prescan_points = self.model.default_prescan_points
        elif self.prescan_points <= 0:
            raise ValueError("prescan_points must be positive.")
        logger.info(f"Prescan points: {self.prescan_points}\n")

        # make instance of param space
        # this automatically initializes the parameters
        self.global_param_space = ParamSpace(model=self.model,
                                             decay=self.decay)

        # make dummy optimal point
        self.global_max = Point(model=self.model)

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
                                          model = self.model)

        # if prescan fails, remove directory and raise an error
        except TimeoutError:

            # delete directory
            self.delete_run_directory()

            # raise error
            raise

        # info message about prescan
        logger.debug(f"Analyzing prescan with {self.prescan_parser.num_unfiltered_points} points")
        logger.debug(f"{self.prescan_parser.num_filtered_points} passed filters\n")

        # shrink param space based on the points contained by it
        self.prescan_parser.shrink_param_space_bounds(self.global_param_space)

        # print bounds table for new global parameter space
        logger.info("Found the following ranges from the prescan:")
        self.global_param_space.log_bounds_table()

        # get scan density
        density = prescan_points / self.global_param_space.volume()

        # get new points
        self.global_max = self.prescan_parser.get_max_xb_point(self.decay)

        # check ratio of prescan max xb in fb to limit_target
        if self.use_adaptive_precision:
            if self.limit_target is None:
                raise ValueError("Limit target must be specified for adaptive precision.")
            ratio = self.global_max.xb * 1000 / self.limit_target
            max_xb = self.global_max.xb * 1000
            formatted_max_xb = f"{max_xb:.2e}" if max_xb < 0.1 or max_xb >= 100 else f"{max_xb:.2f}"
            if ratio < Precision.COARSE.threshold():
                logger.info(f"Prescan max of {formatted_max_xb} fb is insensitive to limit target {self.limit_target} fb.")
                self.precision = Precision.INSENSITIVE
            if ratio > Precision.SATURATED.threshold():
                logger.info(f"Prescan max of {formatted_max_xb} fb is more than {Precision.SATURATED.threshold()} times the limit target {self.limit_target} fb.")
                self.precision = Precision.SATURATED

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

        logger.info("Running mean shift optimization...\n")

        # get scan start time
        scan_start = time.time()

        # initialize output directories and files
        self.initialize_output("meanshift")

        # run prescan
        self.run_prescan()

        # Define helper functions (as inner functions because only for meanshift implementation)

        # Returns a list of initial positions for shifters
        def initial_positions(num_optimizers: int) -> Tuple[Point]:
            random_positions = []

            for _ in range(num_optimizers):
                random_positions.append(self.global_param_space.random_point())

            return tuple(random_positions)

        initial_pos_set = initial_positions(num_optimizers)

        # Create PointSampler object
        point_sampler = PointSampler(model = self.model,
                                     out_dir = self.out_dir,
                                     subdir_name = "meanshift")

        logger.debug("Initial points:\n" + "\n".join(f"\t{p}" for p in initial_pos_set) + "\n")

        for i, initial_pos in enumerate(initial_pos_set):
            label = f"MeanShiftOptimizer-{i}"

            MeanShiftOptimizer(
                label=label,
                initial_pos=initial_pos,
                global_param_space=self.global_param_space,
                point_sampler=point_sampler,
                optimizer_config=self.optimizer_config
            ).run()

        # SCAN LOGIC END HERE

        # sort summary file
        # TODO: make sure to sort the tsv summary file as well
        sort_tsv_file(self.summary_name)

        # get total scan time
        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # finalize the run
        self.finalize(strategy="meanshift",
                      scan_time=scan_time,
                      num_points=num_optimizers)

    def run_zoom_optimization(self,
                              niter: int,
                              num_points: Optional[int] = None) -> None:
        """
        Run a zoom optimization.

        Args:
            num_points (Optional[int]): Number of points to use in the first iteration.
            niter (int): Number of iterations to run. Leave as -1 to run until natural ending criteria are met.
        """

        logger.info(f"Running zoom optimization with {num_points} points\n")

        # get scan start time
        scan_start = time.time()

        # if num_points isn't given, use default_zoom_points
        if num_points is None:
            num_points = self.model.default_zoom_points
        elif num_points <= 0:
            raise ValueError("num_points must be greater than 0 for zoom optimization.")

        # initialize output directories and files
        self.initialize_output("zoom")

        # run prescan
        self.run_prescan()

        # make a list of all zoom optimizers based on bimodal distribution tests
        if self.precision != Precision.INSENSITIVE and self.precision != Precision.SATURATED:
            all_zoom_optimizers = self.create_zoom_optimizers(self.global_param_space, num_points)

            # list of which zoom optimizers are running
            running_list = [True]

            # to keep count of which iteration the scan is on
            iter = 0

            while any(running_list):

                # check if user has added a set number of iterations
                if niter > 0 and iter >= niter:
                    logger.info(f"Ending after {niter} iterations as requested")
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

                        # keep track of the maximum precision used
                        if self.precision is None:
                            self.precision = Precision.LOW
                        if zoom_optimizer.precision is not None:
                            self.precision = max(self.precision, zoom_optimizer.precision)

                    # keeping track of which zoom optimizers are running
                    running_list.append(zoom_optimizer.is_running)
                
                # count iteration
                iter += 1

        # get total scan time
        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # finalize the run
        self.finalize(strategy="zoom",
                      scan_time=scan_time,
                      num_points=num_points,
                      precision=self.precision)

    def get_param_spaces(self,
                         param_space: ParamSpace) -> List[ParamSpace]:

        """
        Create list of param spaces based on splits from the global parameter space.

        Args:
            param_space (ParamSpace): Global parameter space
        """

        logger.debug("Splitting global param space...")

        # Initialize Lists to hold the current param spaces and the final param spaces
        current_param_space_list = [param_space]
        final_param_space_list =[]

        # Iterate through the current unchecked param spaces
        while current_param_space_list:

            # Remove the first param space and hold on to it as the current param space
            current = current_param_space_list.pop(0)
            param_names = current.parameter_names

            # --- Step 1: 1D Splitting Pass ---
            did_split = False
            for parameter_name in param_names:
                all_splits = self.prescan_parser.get_param_space_splits(
                    param_name=parameter_name,
                    decay=self.decay,
                    param_space=current
                )
                if all_splits:
                    new_param_spaces = current.split_range(
                        param_name=parameter_name, split_values=all_splits
                    )
                    current_param_space_list.extend(new_param_spaces)
                    did_split = True
                    break  # Exit 1D splitting loop

            if did_split:
                continue  # Skip 2D pass if 1D split occurred

            # --- Step 2: 2D Splitting Pass ---
            for i in range(len(param_names)):
                for j in range(i + 1, len(param_names)):
                    param_x, param_y = param_names[i], param_names[j]
                    split_dict = self.prescan_parser.get_2d_density_splits(
                        param_x, param_y, decay=self.decay, param_space=current
                    )
                    if split_dict:
                        subspaces = [current]
                        for pname, split_vals in split_dict.items():
                            subspaces = [s for ps in subspaces for s in ps.split_range(pname, split_vals)]
                        current_param_space_list.extend(subspaces)
                        did_split = True
                        break  # Exit inner 2D loop
                if did_split:
                    break  # Exit outer 2D loop

            if not did_split:
                final_param_space_list.append(current)

        logger.debug(f"{len(final_param_space_list)} param spaces created based on global param space.")

        logger.debug("Shrinking each param space...")

        # Shrink the param spaces in final_param_space_list
        for space in final_param_space_list:

            # Shrink the param space
            self.prescan_parser.shrink_param_space_bounds(param_space=space)
        
        return final_param_space_list

    def create_zoom_optimizers(self,
                               param_space: ParamSpace,
                               num_points: int) -> List[ZoomOptimizer]:

        """
        Create list of zoom optimizers based on the parameter space.

        Args:
            param_space (ParamSpace): Global parameter space
            num_points (int): Number of points to use in the first iteration.
        """

        # Retrieve the list of param spaces
        list_of_param_spaces = self.get_param_spaces(param_space)

        # Print info about the number of param spaces created
        logger.info(f"Creating {len(list_of_param_spaces)} zoom optimizers:")
        logger.info("---------------------------------------------")

        # List that holds all the zoom optimizers created
        all_zoom_optimizers: List[ZoomOptimizer] = []

        # Get list of points for optimizers
        points_per_optimizer_list = self.distribute_points(list_of_param_spaces, num_points)

        # Create PointSampler object
        point_sampler = PointSampler(model = self.model,
                                     out_dir = self.out_dir,
                                     subdir_name = "zoom")

        # Create zoom optimizers based on param spaces
        for i, space in enumerate(list_of_param_spaces):
            zoom_optimizer = ZoomOptimizer(
                num_points = points_per_optimizer_list[i],
                param_space = space,
                precision = self.precision,
                limit_target = self.limit_target,
                starting_max = self.global_max,
                point_sampler = point_sampler,
                optimizer_config = self.optimizer_config,
                label = f'ZoomOptimizer-{i}'
            )

            logger.info(f"Initializing {zoom_optimizer.label} with {points_per_optimizer_list[i]} points")

            # Append zoom optimizers to all_zoom_optimizers list
            all_zoom_optimizers.append(zoom_optimizer)
        
        logger.info("---------------------------------------------\n")

        # Return list of all zoom optimizers
        return all_zoom_optimizers

    def distribute_points(self,
                          param_space_list: List[ParamSpace],
                          num_points: int) -> Tuple[int]:

        """
        Distribute the points among the list of param spaces based on their volume.

        Args:
            param_space_list (List[ParamSpace]): List of all parameter spaces from get_param_spaces.
            num_points (int): Number of points to use in the first iteration.
        """

        # Retrieve number of param spaces
        num_param_spaces = len(param_space_list)

        logger.debug(f'Distributing {num_points} among {num_param_spaces} zoom optimizers.')

        # Initialize list of param space volumes
        volumes = np.array([self.prescan_parser.estimate_effective_volume_by_count(space) for space in param_space_list])

        # Retrieve total volume of all param spaces
        total_volume = volumes.sum()

        # Calculate volume by points & how many points each zoom optimizer scans
        points_per_vol_array = (volumes / total_volume) * num_points

        # Round the number of points needed for the scan
        points_array = np.round(points_per_vol_array, decimals=0, out=None).astype(int)

        # Assign rounded points to the points_per_optimizer_array
        points_per_optimizer_array = points_array

        # Minimum points assignment
        min_points = min(num_points/10,20)
        logger.debug(f"Minimum points per zoom optimizer: {min_points}")

        # Distribute remaining points to indices by param space volume size
        for i in range(num_param_spaces):
    
            if points_array[i] < min_points:
                points_per_optimizer_array[i] = min_points
            
        # Return to call
        return tuple(points_per_optimizer_array.tolist())
    
    def run_bayesian_optimizer(self,
                               num_points: int) -> None:
        # get scan start time
        scan_start = time.time()

        self.initialize_output("bayes")

        # if num_points isn't given, use num_starting_points
        if num_points < 0:
            num_points = self.num_starting_points

        # run prescan
        self.run_prescan()

        # move into the working directory for scans
        os.chdir(self.out_dir)

        # create optimizer
        bayesian_optimizer = BayesianOptimizer(model=self.model,
                                               decay=self.decay,
                                               random_point=num_points,
                                               n_points=num_points,
                                               param_space=self.global_param_space)

        # run scan
        bayesian_optimizer.run()

        scan_end = time.time()
        scan_time = (scan_end - scan_start)

        # finalize the run
        self.finalize(strategy="bayes",
                      scan_time=scan_time,
                      num_points=num_points)

    def finalize(self,
                 strategy: str,
                 scan_time: float,
                 num_points: Optional[int] = None,
                 precision: Optional[Precision] = None) -> None:
        """
        Finalize the scan by saving metadata and cleaning up.

        Args:
            strategy (str): The optimization strategy used.
            scan_time (float): The total time taken for the scan.
            num_points (int, optional): Number of points to use in the first iteration. Defaults to -1.
            precision (Precision, optional): The precision level for the scan. Defaults to Precision.MEDIUM.
        """

        # print message indicating scan is done
        logger.info("Done!")

        # print out scan time
        logger.info(f"Scan took {datetime.timedelta(seconds=int(scan_time))} (hh:mm:ss)\n")

        # write time info to details file
        with open(self.details_name, "a") as details:
            details.write(f"Scan took {datetime.timedelta(seconds=int(scan_time))} (hh:mm:ss)\n")

        # save metadata
        save_run_metadata(out_dir=self.out_dir,
                          strategy=strategy,
                          num_points=num_points,
                          precision=precision)

    def delete_run_directory(self) -> None:
        """
        Delete the run directory if it exists.
        """
        if os.path.exists(self.out_dir):
            logger.debug(f"Removing existing directory {self.out_dir}")
            shutil.rmtree(self.out_dir)
