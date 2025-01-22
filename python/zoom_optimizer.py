#!/usr/bin/env python3

# standard libraries
import datetime
import logging
import shutil
import time

# third-party libraries
import pandas as pd

# local modules
from utils.config_loader import ConfigLoader
from utils.file_utils import scan_dir
from utils.params import Params
from utils.point import Point
from utils.point_sampler import PointSampler

class ZoomOptimizer:

    def __init__(self,
                 params: 'Params',
                 num_points: int,
                 use_multiprocessing: bool,
                 starting_max: 'Point',
                 config_loader: ConfigLoader,
                 label: str = ""):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # some basic scanner information
        self.params = params
        self.decay = params.decay
        self.num_points = num_points
        self.local_max = Point(starting_max.model_name)
        self.global_max = starting_max
        self.label = label
        self.top_percentile = {}
        self.top_percentile_xb = None
        self.global_xb_fail = 0
        self.local_xb_fail = 0
        self.is_running = True
        self.local_history = []

        # get zoom configuration from config file
        self.config_loader = config_loader
        try:
            self.strategy: str = self.config_loader.get('zoom', 'strategy')
            self.zoom_percentile: int = self.config_loader.get('zoom', 'zoom_percentile')
            self.parameter_zoom_rate: float = self.config_loader.get('zoom', 'parameter_zoom_rate')
            self.density_growth_rate: float = self.config_loader.get('zoom', 'density_growth_rate')
            self.min_points_per_iteration: int = self.config_loader.get('zoom', 'min_points_per_iteration')
        except KeyError as e:
            self.logger.error(e)
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error: {e}")
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
        out_dir = scan_dir(model_name = params.model_name,
                           decay = params.decay,
                           masses = params.masses)

        # create PointSampler object
        self.point_sampler = PointSampler(out_dir = out_dir,
                                          model_name = params.model_name,
                                          use_multiprocessing = use_multiprocessing,
                                          config_loader = config_loader,
                                          use_file_dir = True)

        # get output information file names
        output_file_postfix = f"{self.params.model_name}_{self.decay}_{self.params.masses}.txt"
        self.summary_name = out_dir + "scan_summary_" + output_file_postfix
        self.tsv_summary_name = out_dir + "scan_tsv_summary_" + output_file_postfix
        self.prescan_details_name = out_dir + "files/details/prescan_details_" + output_file_postfix
        self.details_name = out_dir + "files/details/scan_details_" + self.label + "_" + output_file_postfix

        # copy prescan details file to zoom optimizer details file
        shutil.copy(self.prescan_details_name,self.details_name)

    def run(self,
            iter: int,
            global_max: 'Point') -> None:

        # get time of iteration start
        iter_start = time.time()

        # save global_max as member variable
        self.global_max = global_max

        # get iteration identifier
        iter_label = f"{iter:04d}"
        if self.label:
            identifier = self.label + "-Iteration-" + iter_label
        self.logger.info(f"Iteration: {identifier}")

        # make sure num_points doesn't drop below min_points_per_iteration
        if self.num_points < self.min_points_per_iteration:
            self.logger.debug(f'{self.num_points} is below the minimum, requesting {self.min_points_per_iteration} points instead')
            self.num_points = self.min_points_per_iteration

        # Create scan_parser using the point_sampler class
        self.scan_parser = self.point_sampler.sample_points(params = self.params,
                                                            num_points_requested = self.num_points,
                                                            identifier = identifier)
        
        # get new point as the maximum from the current scan
        new_max = self.scan_parser.get_max_xb_point(self.decay)

        # store the previous point
        self.local_max_old = self.local_max

        # if new point is better than the local max point, replace it
        if new_max > self.local_max:
            self.local_max = new_max

        # if a new optimal point is found, write information to the summary file
        if self.is_new_global_max(new_max):

            # write max xb point summary to info file
            self.write_summary(identifier)

            # write max xb point raw .tsv line to info file
            self.scan_parser.write_max_xb_line(self.tsv_summary_name)

        # write scan details to details file
        self.write_details(identifier=identifier,
                           new_max=new_max)

        # add to a counter if new point is less than half of the global max
        if new_max < self.global_max * 0.5:
            self.global_xb_fail += 1
        else:
            self.global_xb_fail = 0
        
        # end the ZoomOptimizer if counter reaches 2
        if self.global_xb_fail >= 2:
            self.is_running = False
            self.logger.info("Local max is consistently less than half of global max")
            self.logger.info("Terminating zoom optimizer")
            details = open(self.details_name,"a")
            details.write("Local max is consistently less than half of global max")
            details.write("Terminating zoom optimizer")
            details.close()
        
        # get a sorted list of the history of the local max xb
        sorted_history = sorted(self.local_history, key=lambda point: point.xb)

        if len(sorted_history) >= 5:
            # if new points are on an upward trend, run this code
            if self.local_history[-1] >= self.local_history[-2]:
                # if point is less than 5% higher than the 2nd highest point twice in a row, end scan
                if new_max < sorted_history[-2] * 1.05:
                    self.local_xb_fail += 1
                    if self.local_xb_fail >= 2:
                        self.is_running = False
                        self.logger.info("Local max is increasing by less than 5%")
                        self.logger.info("Terminating zoom optimizer")
                        details = open(self.details_name,"a")
                        details.write("Local max is increasing by less than 5%")
                        details.write("Terminating zoom optimizer")
                        details.close()
                # reset local_xb_fail
                else:
                    self.local_xb_fail = 0
            else:
                # if point is less than 2nd highest point, end scan
                if new_max < sorted_history[-2]:
                    self.is_running = False
                    self.logger.info("Local max is not increasing")
                    self.logger.info("Terminating zoom optimizer")
                    details = open(self.details_name,"a")
                    details.write("Local max is not increasing")
                    details.write("Terminating zoom optimizer")
                    details.close()

        # store history of local max of xb
        self.local_history.append(new_max)

        # call the appropriate zoom method based on the strategy
        match self.strategy:

            # zoom in using percentile
            case "percentile":
                self.percentile_zoom()

            # zoom in using rate
            case "rate":
                self.rate_zoom()

            # all other cases
            case _:
                raise ValueError(f"Unrecognized zoom strategy: {self.strategy}")

        # get iteration end time
        iter_end = time.time()
        iter_time = iter_end - iter_start

        # print iteration time to screen
        self.logger.info(f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n")
            
        return new_max

    # write max xb point summary to info file
    def write_summary(self, identifier) -> None:
        summary = open(self.summary_name,"a")
        summary.write(self.local_max.format_xb())
        for name, par in self.params.parameters.items():
            summary.write(f"\t{self.local_max.get_val(name):1.{par.precision}f}")
        summary.write(f"\t{identifier}\n")
        summary.close()

    # write to details file
    def write_details(self,
                      identifier: str,
                      new_max: 'Point') -> None:

        # get point density from ranges
        density = self.num_points / self.params.volume()

        # TODO: Add details about R11, R21, R31
        details = open(self.details_name,"a")
        details.write(f"Iteration = {identifier}\n")
        details.write("--------------------\n")
        details.write(f"Using {self.point_sampler.total_points_run} scan points\n")
        details.write(f"Scan density = {density:.3E}\n")
        details.write(f"{self.point_sampler.nwidth}/{self.point_sampler.total_points_run} pass width check\n")
        details.write(f"{self.point_sampler.nbounds}/{self.point_sampler.total_points_run} pass bounds check\n")
        details.write(f"{self.point_sampler.nsignals}/{self.point_sampler.total_points_run} pass signals check\n")
        details.write(f"{self.point_sampler.npass}/{self.point_sampler.total_points_run} pass all checks\n")
        details.write("--------------------\n")
        details.write(f"New max xsec*BR = {new_max.format_xb()}\n")
        details.write(f"Local max xsec*BR = {self.local_max.format_xb()}\n")
        details.write(f"Global max xsec*BR = {self.global_max.format_xb()}\n")
        details.write(f"Found new global max point: {self.is_new_global_max(new_max)}\n")
        details.write("--------------------\n")
        for par in self.params.parameter_names:
            details.write(f"{par}:\n")
            details.write(f"  range = {self.params.parameter_value(par).format_range()}\n")
            if self.is_new_global_max(new_max):
                details.write(f"  new global max value = {self.local_max.format_param(par)}\n")
                details.write(f"  diff. = {self.local_max.format_diff(self.local_max_old,par)}\n")
                details.write(f"  rel. diff. = {self.local_max.format_diff_frac(self.local_max_old,par)}\n")
        details.write("--------------------\n")
        details.close()

    # check if a new global max has been found
    def is_new_global_max(self,
                          new_max: 'Point') -> bool:
        return new_max > self.global_max

    # method to zoom in based on a percentile cut on xb
    def percentile_zoom(self) -> None:

        # minimum number of points required before zooming in
        min_points = 10

        # percentile threshold that can be adjusted on the fly
        percentile_threshold = self.zoom_percentile

        # get an array of xb results
        xb_array = self.scan_parser.get_xb(self.decay)

        # if top_percentile_xb has already been filled, add it to current xb_array
        if self.top_percentile_xb is not None:
            xb_array = pd.concat([xb_array, self.top_percentile_xb])

        # ensure min_points are looked
        if len(xb_array) * (1.0 - percentile_threshold) < min_points:
            percentile_threshold = 1.0 - min_points / xb_array.size

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # create a threshold to look at the top percentile of xb points
        xb_threshold = xb_array.quantile(percentile_threshold)

        # get top percentile of xb
        self.top_percentile_xb = xb_array[xb_array > xb_threshold]

        # dictionaries to update low and high in parameters
        low_dict = {}
        high_dict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in self.scan_parser.parameter_arrays.items():
            # if param is already in top_percentile, add top_percentile to values
            if param in self.top_percentile:
                values = pd.concat([values, self.top_percentile[param]])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > xb_threshold]
            # set lows and highs of each parameter
            low_dict[param] = self.top_percentile[param].min()
            high_dict[param] = self.top_percentile[param].max()

        # update params lows and highs using dictionaries
        self.params.update_low_high(low_dict, high_dict)

        # calculate the new number of points based on the remaining xb range
        height_ratio = (xb_array.max() - xb_threshold) / (xb_array.max() - xb_array.min())
        self.num_points = int(self.num_points * height_ratio * (1.0 + self.density_growth_rate))

        return

    # method to zoom in based on a fixed rate
    def rate_zoom(self) -> None:

        # parameter scaling factor
        range_scale = 1.0 - self.parameter_zoom_rate

        # get volume before zooming
        volume_old = self.params.volume()

        # set new low and high values
        self.params.scale_ranges(self.local_max,range_scale)

        # get volume after zooming
        volume_new = self.params.volume()
        volume_ratio = volume_new / volume_old

        # step down num_points
        self.num_points = int(self.num_points * volume_ratio * (1.0 + self.density_growth_rate))
    
        return
