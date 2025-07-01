#!/usr/bin/env python3

"""
Zoom-based optimizer for refining scalar model parameter scans.

This module defines the ZoomOptimizer class, which iteratively focuses
sampling in promising regions of parameter space based on cross-section
times branching ratio (xb) metrics. The optimizer can operate in either
a fixed-rate zoom mode or a percentile-based zoom mode.
"""

# standard libraries
import datetime
import os
import shutil
import time
from typing import Dict, Optional

# third-party libraries
import pandas as pd

# local modules
from utils.config_loader import ConfigLoader
from utils.exceptions import NoPointsPassedError
from utils.file_utils import scan_dir
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point
from utils.point_sampler import PointSampler
from utils.precision_utils import Precision
from utils.tsv_utils import write_point_to_summary_file

# get logger
import logging
logger = logging.getLogger(__name__)

class ZoomOptimizer:
    """
    Optimizer that refines a parameter space scan using local zooming strategies.

    The ZoomOptimizer performs iterative scanning by concentrating sampling
    around regions of high xb values. It supports two zooming strategies:
    percentile-based and fixed-rate. It tracks local and global maxima, manages
    scan density, and controls stopping conditions based on scan performance.
    """

    def __init__(self,
                 param_space: ParamSpace,
                 num_points: int,
                 starting_max: Point,
                 point_sampler: PointSampler,
                 config_loader: ConfigLoader,
                 label: str,
                 precision: Optional[Precision] = None,
                 limit_target: float = -1.0) -> None:
        """
        Initializes a ZoomOptimizer instance with configuration and scan parameters.

        Args:
            param_space (ParamSpace): The parameter space to scan.
            num_points (int): Initial number of scan points per iteration.
            starting_max (Point): The initial best point found prior to zooming.
            point_sampler (PointSampler): PointSampler object used to sample points.
            config_loader (ConfigLoader): Configuration loader for reading zoom settings.
            label (str): A string label identifying the scan.
            precision (Optional[Precision]): The precision level for the scan.
            limit_target (float, optional): The target experimental limit for setting precision. Defaults to -1.0.
        """

        # some basic scanner information
        self.param_space = param_space
        self.num_points = num_points
        self.local_max = starting_max.copy(0.0)
        self.global_max = starting_max.copy()
        self.label = label
        self.top_percentile = {}
        self.top_percentile_xb = None
        self.global_xb_fail = 0
        self.local_xb_fail = 0
        self.is_running = True
        self.local_history = []
        self.point_sampler = point_sampler
        self.run_test_job = True
        self.limit_target = limit_target

        if precision is None:
            self.use_adaptive_precision = True
            self.precision = Precision.COARSE
        else:
            self.use_adaptive_precision = False
            self.precision = precision

        # get zoom configuration from config file
        self.config_loader = config_loader
        try:
            self.strategy: str = self.config_loader.get('zoom', 'strategy')
            self.global_xb_fail_threshold: float = self.config_loader.get('zoom', 'global_xb_fail_threshold')
            self.global_xb_fail_count: int = self.config_loader.get('zoom', 'global_xb_fail_count')
            self.local_xb_fail_threshold: Dict[str,float] = self.config_loader.get_param_levels('zoom', 'local_xb_fail_threshold')
            self.local_xb_fail_count: Dict[str,int] = self.config_loader.get_param_levels('zoom', 'local_xb_fail_count')
            self.zoom_percentile: Dict[str,int] = self.config_loader.get_param_levels('zoom', 'zoom_percentile')
            self.parameter_zoom_rate: Dict[str,float] = self.config_loader.get_param_levels('zoom', 'parameter_zoom_rate')
            self.density_growth_rate: Dict[str,float] = self.config_loader.get_param_levels('zoom', 'density_growth_rate')
            self.min_points_per_iteration: Dict[str,int] = self.config_loader.get_param_levels('zoom', 'min_points_per_iteration')
            self.precision_threshold_low: float = self.config_loader.get('precision', 'threshold_low')
            self.precision_threshold_medium: float = self.config_loader.get('precision', 'threshold_medium')
            self.precision_threshold_high: float = self.config_loader.get('precision', 'threshold_high')
        except Exception as e:
            logger.exception(e)
            raise

        # supported strategies
        allowed_strategies = {"rate","percentile"}

        # check the strategy and throw an error if it is not supported
        if self.strategy not in allowed_strategies:
            raise ValueError(
                f"Unrecognized zoom strategy: '{self.strategy}'. "
                f"Allowed strategies are: {', '.join(allowed_strategies)}."
            )

        # set output directory
        out_dir = scan_dir(model = self.model,
                           decay = self.decay)

        # get output information file names
        output_file_postfix = f"{self.model.name}_{self.decay}_{self.model.mass_string}"
        self.summary_name = os.path.join(out_dir,f"summary_zoom_{output_file_postfix}.tsv")
        self.tsv_summary_name = os.path.join(out_dir,f"summary_zoom_tsv_{output_file_postfix}.tsv")
        self.prescan_details_name = os.path.join(out_dir,"zoom","details",f"prescan_details_{output_file_postfix}.txt")
        self.details_name = os.path.join(out_dir,"zoom","details",f"scan_details_{self.label}_{output_file_postfix}.txt")

        # copy prescan details file to zoom optimizer details file
        shutil.copy(self.prescan_details_name,self.details_name)

    @property
    def model(self) -> Model:
        """Returns the scalar model associated with the parameter space."""
        return self.param_space.model

    @property
    def decay(self) -> str:
        """Returns the decay channel being evaluated (e.g., 'H->SS')."""
        return self.param_space.decay

    @property
    def precision(self) -> Optional[Precision]:
        """
        Returns the precision level of the scan.
        """
        return self._precision

    @precision.setter
    def precision(self, value: Optional[Precision]) -> None:
        """
        Sets the precision level of the scan.
        """
        self._precision = value

    def run(self,
            iter: int,
            global_max: Point) -> Point:
        """
        Executes one iteration of the zoom optimization process.

        This includes point sampling, updating the local maximum, applying zoom,
        logging details, and checking termination conditions.

        Args:
            iter (int): The iteration number.
            global_max (Point): The current global maximum point across all iterations.

        Returns:
            Point: The best point found in this iteration.
        """

        # get time of iteration start
        iter_start = time.time()

        # save global_max as member variable
        self.global_max = global_max

        # get iteration identifier
        identifier = f"{self.label}-Iteration-{iter:04d}"
        logger.info(f"Iteration: {identifier}")

        # make sure num_points doesn't drop below min_points_per_iteration
        if self.num_points < self.min_points_per_iteration[str(self.precision)]:
            logger.debug(f'{self.num_points} is below the minimum, requesting {self.min_points_per_iteration[str(self.precision)]} points instead')
            self.num_points = self.min_points_per_iteration[str(self.precision)]

        # flag to indicate if zooming should be done
        do_zoom = True

        # create scan_parser using the point_sampler class
        try:
            self.scan_parser = self.point_sampler.sample_points(param_space = self.param_space,
                                                                num_points_requested = self.num_points,
                                                                identifier = identifier,
                                                                run_test_job = self.run_test_job)
        # if point sampling times out make a dummy new_max
        except TimeoutError:
            self.termination_message("No output detected")
            self.termination_message("Using empty point as new max")
            new_max = Point(xb = 0.0,
                            model = self.model,
                            par_vals = self.local_max.parameter_values)
            do_zoom = False
        # if no points pass the filters, make a dummy new_max and end the optimizer
        except NoPointsPassedError:
            self.termination_message("No points passed the filters")
            new_max = Point(xb = 0.0,
                            model = self.model,
                            par_vals = self.local_max.parameter_values)
            do_zoom = False
            self.is_running = False
        # otherwise get new point as the maximum from the current scan
        else:
            self.run_test_job = False  # no need to run test job again
            new_max = self.scan_parser.get_max_xb_point(self.decay)

        # store the previous point
        self.local_max_old = self.local_max

        # if new point is better than the local max point, replace it
        self.local_max = max(self.local_max, new_max)

        # adaptive precision adjustment based on xb value
        if self.use_adaptive_precision:
            self.update_precision(self.local_max)

        # if a new optimal point is found, write information to the summary file
        if self.is_new_global_max(new_max):

            # write max xb point summary to summary file
            write_point_to_summary_file(file_name=self.summary_name,
                                        point=new_max,
                                        identifier=identifier)

            # write max xb point raw .tsv line to summary tsv file
            new_max.write_tsv_to_file(self.tsv_summary_name)

        # write scan details to details file
        self.write_details(identifier=identifier,
                           new_max=new_max)

        # check stopping conditions
        if self.check_stopping_conditions(new_max):
            self.is_running = False
            do_zoom = False
            self.termination_message("Terminating zoom optimizer")

        # store history of local max of xb
        self.local_history.append(new_max)

        if do_zoom:
            # call the appropriate zoom method based on the strategy
            # zoom in using percentile
            if self.strategy == "percentile":
                self.percentile_zoom()
            # zoom in using rate
            elif self.strategy == "rate":
                self.rate_zoom()
            # all other cases
            else:
                raise ValueError(f"Unrecognized zoom strategy: {self.strategy}")

        # get iteration end time
        iter_end = time.time()
        iter_time = iter_end - iter_start

        # record iteration time to screen
        self.termination_message(f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n")

        return new_max

    def update_precision(self,
                         test_point: Point) -> None:
        """
        Updates the precision based on the new maximum xb value.

        Args:
            test_point (Point): The Point to test against self.limit_target.
        """
        if abs(self.limit_target) < 1e-12:
            raise ValueError("Cannot adapt precision: limit_target is effectively zero")
        ratio = test_point.xb * 1000 / self.limit_target
        if self.precision_threshold_low < ratio <= self.precision_threshold_medium and self.precision != Precision.LOW:
            logger.info(f"Adjusting precision to LOW (ratio = {ratio:.2f})")
            self.precision = Precision.LOW
        elif self.precision_threshold_medium <= ratio < self.precision_threshold_high and self.precision != Precision.MEDIUM:
            logger.info(f"Adjusting precision to MEDIUM (ratio = {ratio:.2f})")
            self.precision = Precision.MEDIUM
        elif self.precision_threshold_high <= ratio and self.precision != Precision.HIGH:
            logger.info(f"Adjusting precision to HIGH (ratio = {ratio:.2f})")
            self.precision = Precision.HIGH

    def check_stopping_conditions(self, new_max: Point) -> bool:
        """
        Checks stopping conditions and updates internal state.

        Returns:
            bool: True if optimization should stop, False otherwise.
        """
        # Global: new point < global_xb_fail_threshold of current global max
        if new_max < self.global_max * self.global_xb_fail_threshold:
            self.global_xb_fail += 1
            if self.global_xb_fail >= self.global_xb_fail_count:
                self.termination_message(f"Local max is consistently less than {int(self.global_xb_fail_threshold*100)}% of global max")
                return True
        else:
            self.global_xb_fail = 0

        # Local: based on improvement history
        if len(self.local_history) >= 5:
            last = self.local_history[-1]
            second_last = self.local_history[-2]
            second_best = sorted(self.local_history, key=lambda pt: pt.xb)[-2]

            # If still improving, but not by enough
            if last >= second_last:
                new_max_threshold = self.local_xb_fail_threshold[str(self.precision)]
                if new_max < second_best * (1.0 + new_max_threshold):
                    self.local_xb_fail += 1
                    if self.local_xb_fail >= self.local_xb_fail_count[str(self.precision)]:
                        self.termination_message(f"Local max is increasing by less than {new_max_threshold*100:.1f}%")
                        return True
                else:
                    self.local_xb_fail = 0
            elif new_max < second_last:
                self.termination_message("Local max is not increasing")
                return True

        return False

    def write_details(self,
                      identifier: str,
                      new_max: Point) -> None:
        """
        Appends detailed scan results and parameter updates to the details file.

        Args:
            identifier (str): A unique label for the current iteration.
            new_max (Point): The new maximum point found in the current iteration.
        """

        # get point density from ranges
        density = self.num_points / self.param_space.volume()

        with open(self.details_name,"a") as details:
            content = f"Iteration = {identifier}\n"
            content += "--------------------\n"
            content += f"Using {self.point_sampler.total_points_run} scan points\n"
            content += f"Scan density = {density:.3E}\n"
            content += f"{self.point_sampler.n_width}/{self.point_sampler.total_points_run} pass width check\n"
            content += f"{self.point_sampler.n_bounds}/{self.point_sampler.total_points_run} pass bounds check\n"
            content += f"{self.point_sampler.n_signals}/{self.point_sampler.total_points_run} pass signals check\n"
            content += f"{self.point_sampler.n_pass}/{self.point_sampler.total_points_run} pass all checks\n"
            content += "--------------------\n"
            content += f"New max xsec*BR = {new_max.format_xb()}\n"
            content += f"Local max xsec*BR = {self.local_max.format_xb()}\n"
            content += f"Global max xsec*BR = {self.global_max.format_xb()}\n"
            content += f"Found new global max point: {self.is_new_global_max(new_max)}\n"
            content += "--------------------\n"
            for par in self.param_space.parameter_names:
                content += f"{par}:\n"
                content += f"  range = {self.param_space.parameter_ranges[par].format_range()}\n"
                if self.is_new_global_max(new_max):
                    content += f"  new global max value = {self.local_max.format_param(par)}\n"
                    content += f"  diff. = {self.local_max.format_diff(self.local_max_old,par)}\n"
                    content += f"  rel. diff. = {self.local_max.format_diff_frac(self.local_max_old,par)}\n"
            content += "--------------------\n"
            details.write(content)

    def termination_message(self,
                            message: str) -> None:
        """
        Logs and writes a termination-related message to the details file.

        Args:
            message (str): The message to record.
        """
        logger.info(message)
        with open(self.details_name,"a") as details:
            details.write(message+"\n")

    def is_new_global_max(self,
                          new_max: Point) -> bool:
        """
        Determines whether a newly found point is a new global maximum.

        Args:
            new_max (Point): The point to evaluate.

        Returns:
            bool: True if the new point exceeds the current global max, False otherwise.
        """
        return new_max > self.global_max

    def percentile_zoom(self) -> None:
        """
        Updates the parameter space by zooming into the top percentile of high-xb points.

        The zoom level and point selection are determined by configuration-defined
        percentile and density growth settings.
        """

        # minimum number of points required before zooming in
        min_points = 10

        # percentile threshold that can be adjusted on the fly
        percentile_threshold = self.zoom_percentile[str(self.precision)]

        # get an array of xb results
        xb_array = self.scan_parser.get_xb(self.decay)

        # if top_percentile_xb has already been filled, add it to current xb_array
        if self.top_percentile_xb is not None:
            xb_array = pd.concat([xb_array, self.top_percentile_xb])

        # ensure min_points are looked
        if len(xb_array) * (1.0 - percentile_threshold) < min_points:
            percentile_threshold = 1.0 - min_points / xb_array.size

        # make sure percentile threshold is >= 0
        percentile_threshold = max(percentile_threshold, 0.0)

        # create a threshold to look at the top percentile of xb points
        xb_threshold = xb_array.quantile(percentile_threshold)

        # get top percentile of xb
        self.top_percentile_xb = xb_array[xb_array > xb_threshold]

        # dictionaries to update low and high in parameters
        low_dict = {}
        high_dict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in self.scan_parser.input_parameter_arrays.items():
            # if param is already in top_percentile, add top_percentile to values
            if param in self.top_percentile:
                values = pd.concat([values, self.top_percentile[param]])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > xb_threshold]
            # set lows and highs of each parameter
            low_dict[param] = self.top_percentile[param].min()
            high_dict[param] = self.top_percentile[param].max()

        # update params lows and highs using dictionaries
        self.param_space.update_low_high(low_dict, high_dict)

        # calculate the new number of points based on the remaining xb range
        height_ratio = (xb_array.max() - xb_threshold) / (xb_array.max() - xb_array.min())
        self.num_points = int(self.num_points * height_ratio * (1.0 + self.density_growth_rate[str(self.precision)]))

    def rate_zoom(self) -> None:
        """
        Shrinks the parameter space uniformly around the current local maximum.

        The update uses a fixed scaling rate defined in the configuration and
        adjusts point density proportionally to the new parameter space volume.
        """

        # parameter scaling factor
        range_scale = 1.0 - self.parameter_zoom_rate[str(self.precision)]

        # get volume before zooming
        volume_old = self.param_space.volume()

        # set new low and high values
        self.param_space.scale_ranges(self.local_max,range_scale)

        # get volume after zooming
        volume_new = self.param_space.volume()
        volume_ratio = volume_new / volume_old

        # step down num_points
        self.num_points = int(self.num_points * volume_ratio * (1.0 + self.density_growth_rate[str(self.precision)]))
