#!/usr/bin/env python3

"""
Mean-shift-based optimizer for refining scalar model scans.

This module defines the MeanShiftOptimizer class, which adaptively adjusts the
parameter space to locate local maxima of cross-section times branching ratio (xb)
using a kernel-based mean shift approach.
"""

import copy
import datetime
from functools import cached_property
import logging
import os
import shutil
import time

import numpy as np

from utils.config_loader import ConfigLoader
from utils.exceptions import NoPointsPassedError
from utils.file_utils import scan_dir
from utils.math_utils import round_sig
from utils.mean_shift_utils import mean_shift
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point
from utils.point_sampler import PointSampler
from utils.tsv_utils import write_point_to_summary_file, initialize_summary_file

class MeanShiftOptimizer:
    """
    Optimizer that applies mean-shift steps to refine scalar model parameter scans.

    The optimizer performs localized scans, shifting the center of the parameter space
    based on the xb-weighted mean of sampled points. The scan stops based on movement
    sensitivity thresholds or a maximum number of small steps.
    """

    def __init__(
            self,
            label: str,
            initial_pos: Point,
            global_param_space: ParamSpace,
            config_loader: ConfigLoader):
        """
        Initializes a MeanShiftOptimizer instance.

        Args:
            label (str): A label to identify the scan.
            initial_pos (Point): Starting point in parameter space.
            global_param_space (ParamSpace): The overall parameter space used in the scan.
            config_loader (ConfigLoader): Configuration loader containing mean-shift settings.
        """

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        self.global_param_space = global_param_space

        self.label = label

        # get mean shift configuration from config file
        self.config_loader = config_loader
        try:
            self.max_small_steps: int = self.config_loader.get('meanshift', 'max_small_steps')
            self.__stop_mode: int = config_loader.get('meanshift', 'stop_mode')
            self.__stop_sens_par: float = config_loader.get('meanshift', 'stop_sensitivity_par')
            self.__stop_sens_xb: float = config_loader.get('meanshift', 'stop_sensitivity_xb')
            self.__scan_perc: float = config_loader.get('meanshift', 'scan_perc')
            self.__num_points: int = config_loader.get('meanshift', 'num_points')
        except KeyError as e:
            self.logger.error(e)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
            raise

        # Copy of param space so that multiple instances of ms use global param space
        self.local_param_space = copy.deepcopy(global_param_space)

        # Set initial param widths
        for param_range in self.local_param_space:
            center = param_range.center
            extent = (param_range.width * self.__scan_perc) / 2

            param_range.low = (center - extent)
            param_range.high = (center + extent)

        # Set center of new params
        self.local_param_space.reposition_center(initial_pos)

        # Init point sampler
        self.point_sampler = PointSampler(out_dir = self.out_dir,
                                          config_loader = config_loader,
                                          subdir_name = "meanshift")

        # Initialize positions
        init_pos = self.local_param_space.center_point()
        self.__test_position = init_pos
        self.new_position = init_pos
        self.__prev_position = init_pos
        self.max_point = init_pos

        output_file_postfix = f"{self.model.name}_{self.decay}_{global_param_space.mass_string}"
        self.summary_name = os.path.join(self.out_dir,f"summary_meanshift_{output_file_postfix}.tsv")
        self.tsv_summary_name = os.path.join(self.out_dir,f"summary_meanshift_tsv_{output_file_postfix}.tsv")
        self.prescan_details_name = os.path.join(self.out_dir,"meanshift","details",f"prescan_details_{output_file_postfix}.txt")
        self.details_name = os.path.join(self.out_dir,"meanshift","details",f"scan_details_{self.label}_{output_file_postfix}.txt")
        self.walk_pos_file_name = os.path.join(self.out_dir,"meanshift","walk",f"walk_pos_{self.label}_{output_file_postfix}.tsv")
        self.walk_max_file_name = os.path.join(self.out_dir,"meanshift","walk",f"walk_max_{self.label}_{output_file_postfix}.tsv")

        # initialize walk files
        initialize_summary_file(file_name=self.walk_pos_file_name,
                                model=init_pos.model)
        initialize_summary_file(file_name=self.walk_max_file_name,
                                model=init_pos.model)

        # copy prescan details file to zoom optimizer details file
        shutil.copy(self.prescan_details_name,self.details_name)

    @property
    def model(self) -> Model:
        """Returns the scalar model being evaluated."""
        return self.global_param_space.model

    @property
    def decay(self) -> str:
        """Return the decay mode being scanned."""
        return self.global_param_space.decay

    @property
    def label(self) -> str:
        """Return the scan's identifying label."""
        return self.__label

    @label.setter
    def label(self,
                new_label: str) -> None:
        """Sets the scan's identifying label."""
        self.__label = new_label

    @property
    def global_param_space(self) -> ParamSpace:
        """Returns the global (full-range) parameter space."""
        return self.__global_param_space

    @global_param_space.setter
    def global_param_space(self,
                           new_global_param_space: ParamSpace) -> None:
        """Sets the global (full-range) parameter space."""
        self.__global_param_space = new_global_param_space

    @property
    def local_param_space(self) -> ParamSpace:
        """Returns the local parameter space."""
        return self.__local_param_space

    @local_param_space.setter
    def local_param_space(self,
                          new_local_param_space: ParamSpace) -> None:
        """Sets the local parameter space."""
        self.__local_param_space = new_local_param_space

    @cached_property
    def out_dir(self) -> str:
        """Returns the path to the output directory for the model and decay."""
        return scan_dir(model=self.model,
                        decay=self.decay)

    @property
    def num_points(self) -> int:
        """Returns the number of sample points per scan."""
        return self.__num_points

    @num_points.setter
    def num_points(self,
                   new_num_points: int) -> None:
        """Sets the number of sample points per scan."""
        self.__num_points = new_num_points

    def run(self) -> None:
        """
        Executes the full mean-shift optimization loop.

        Iteratively performs parameter scans, applies the mean-shift update rule,
        and writes output to walk, summary, and details files. Stops based on convergence
        or lack of significant parameter movement.
        """

        # get time of mean shift start
        shift_start = time.time()

        # Initialize iteration counter
        iter = -1

        # Initialize counter for number of small steps
        self.n_small_steps = 0

        # Flag to indicate whether iterations should stop
        stop = False

        # Default starting value for identifier
        identifier = self.label

        # Loop until stop condition is met
        while not stop:

            # get time of iteration start
            iter_start = time.time()

            iter += 1

            # get iteration identifier
            identifier = self.label + f"-{iter:04d}"
            self.logger.info(f"Iteration: {identifier}")

            # Create scan_parser using the point_sampler class
            try:
                parser = self.point_sampler.sample_points(param_space = self.local_param_space,
                                                          identifier = identifier,
                                                          num_points_requested = self.num_points,
                                                          good_points_only = False,
                                                          use_multiprocessing = False)
            # if point sampling times out, exit
            except (TimeoutError, NoPointsPassedError):
                self.logger.info(f"No points found. Exiting {identifier}\n")
                return

            arrays = {k: v.to_numpy() for k, v in parser.input_parameter_arrays.items()}
            xb = parser.get_xb(self.decay).to_numpy()

            # Store previous position before calculating a new one
            self.__prev_position = self.new_position

            mean_shift(arrays = arrays,
                       Z = xb,
                       param_space = self.local_param_space,
                       config_loader=self.config_loader)

            # get new position
            self.logger.info("Calculating a point at the new position")
            self.new_position = self.point_sampler.sample_single_point(point=self.local_param_space.center_point(),
                                                                       decay=self.decay,
                                                                       identifier=identifier+"-point")

            # store the highest point that has been checked
            # this can either be from sampling or from the mean-shifted position
            self.max_point = max(
                self.max_point,
                parser.get_max_xb_point(self.decay),
                self.new_position
            )

            stop = self.__stop_check()

            # write scan details to details file
            self.write_details(identifier=identifier,
                               xb=xb)

            # get iteration end time
            iter_end = time.time()
            iter_time = iter_end - iter_start

            self.iteration_termination_message(f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n")

            # NOTE: For debugging
            if self.logger.isEnabledFor(logging.DEBUG):
                test_diff = tuple([self.__stop_sens_par * w for w in self.local_param_space.widths()])
                position_diff = tuple(
                    self.new_position.parameter_values[k] - self.__prev_position.parameter_values[k]
                    for k in self.local_param_space.parameter_names
                )

                self.logger.debug(f"small steps = {self.n_small_steps}")
                self.logger.debug(f"avg xb      = {round_sig(float(np.average(xb)))}")
                self.logger.debug(f"max xb      = {round_sig(np.max(xb))}")
                self.logger.debug(f"volume size = {self.local_param_space.widths()}")
                self.logger.debug(f"curr pos    = {self.local_param_space.center_point()}")
                self.logger.debug(f"prev pos    = {self.__prev_position}")
                self.logger.debug(f"test pos    = {self.__test_position}")
                self.logger.debug(f"reset diff  = {test_diff}")
                self.logger.debug(f"posit diff  = {position_diff}\n")

            # write step details to walk file
            write_point_to_summary_file(file_name=self.walk_pos_file_name,
                                        point=self.new_position)
            write_point_to_summary_file(file_name=self.walk_max_file_name,
                                        point=self.max_point)

        # write max point information to summary files
        write_point_to_summary_file(file_name=self.summary_name,
                                    point=self.max_point,
                                    identifier=identifier)
        self.max_point.write_tsv_to_file(tsv_name=self.tsv_summary_name)

        # get mean shift end time
        shift_end = time.time()
        shift_time = shift_end - shift_start

        # print iteration time to screen
        self.logger.info(f"{self.label} took {datetime.timedelta(seconds=int(shift_time))} (hh:mm:ss)\n")

        return

    def write_details(self,
                      identifier: str,
                      xb: np.ndarray) -> None:
        """Writes parameter space and scan result details for a given iteration.

        Args:
            identifier (str): Identifier for the current iteration.
            xb (np.ndarray): Array of xb values from the scan.
        """
        with open(self.details_name, 'a') as details_file:
            content = f"Iteration = {identifier}\n"
            content += "--------------------\n"
            content += f"Using {self.num_points} scan points\n"
            content += "--------------------\n"
            for name in self.local_param_space.parameter_names:
                content += name + ":\n"
                content += f"  range = {self.local_param_space[name].format_range()}\n"
                content += f"  width = {round_sig(self.local_param_space[name].width)}\n"
            content += "--------------------\n"
            content += f"scan_pts  = {self.num_points}\n"
            content += f"max_pos  = {self.max_point}\n"
            content += f"curr_pos  = {self.new_position}\n"
            content += f"prev_pos  = {self.__prev_position}\n"
            content += f"test_pos  = {self.__test_position}\n"
            content += f"avg_xb    = {round_sig(float(np.average(xb)))}\n"
            content += f"max_xb    = {round_sig(np.max(xb))}\n"
            content += f"new_xb    = {round_sig(self.new_position.xb)}\n"
            content += "--------------------\n"
            details_file.write(content)

    def iteration_termination_message(self,
                                      message: str) -> None:
        """
        Logs and appends a message related to iteration termination.

        Args:
            message (str): The message to log and write.
        """
        self.logger.info(message)
        with open(self.details_name,"a") as details:
            details.write(message+"\n")

    def __stop_check(self) -> bool:
        """
        Determines whether the mean-shift scan should stop.

        Checks whether the center of the parameter space is changing less than a
        configured sensitivity threshold for a specified number of iterations.

        Returns:
            bool: True if the scan should stop, False otherwise.
        """

        # TODO: This should probably also check self.max_point
        # TODO: Revisit these stopping conditions

        comp_point = self.__test_position if self.__stop_mode == 0 else self.__prev_position

        # Check if any parameter changed beyond the sensitivity threshold
        changed = any(
            self.new_position.diff_frac(comp_point, name) > self.__stop_sens_par
            for name in self.local_param_space.parameter_names
        ) or (self.new_position.diff_frac(comp_point, 'xb') > self.__stop_sens_xb)

        if changed:
            self.n_small_steps = 0
            self.__test_position = self.new_position
        else:
            self.n_small_steps += 1

        return self.n_small_steps >= self.max_small_steps
