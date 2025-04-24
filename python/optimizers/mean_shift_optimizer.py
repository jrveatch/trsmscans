#!/usr/bin/env python3

import copy
import datetime
from functools import cached_property
import logging
import os
import shutil
import time

import numpy as np

from utils.config_loader import ConfigLoader
from utils.file_utils import scan_dir
from utils.math_utils import round_sig
from utils.mean_shift_utils import mean_shift
from utils.model import Model
from utils.param_space import ParamSpace
from utils.point import Point
from utils.point_sampler import PointSampler

class MeanShiftOptimizer:

    def __init__(
            self,
            label: str,
            initial_pos: 'Point',
            points: int,
            global_param_space: ParamSpace,
            config_loader: ConfigLoader):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        self.global_param_space = global_param_space

        self.__points = points
        self.__label = label

        # get mean shift configuration from config file
        self.config_loader = config_loader
        try:
            self.max_small_steps: int = self.config_loader.get('meanshift', 'max_small_steps')
            self.__stop_mode: int = config_loader.get('meanshift', 'stop_mode')
            self.__stop_sens_par: float = config_loader.get('meanshift', 'stop_sensitivity_par')
            self.__stop_sens_xb: float = config_loader.get('meanshift', 'stop_sensitivity_xb')
            self.__scan_perc: float = config_loader.get('meanshift', 'scan_perc')
            self.__debug: bool = config_loader.get('meanshift', 'debug')
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
                                          use_file_dir = True)

        # Initialize positions
        self.__test_position = self.local_param_space.vol_position
        self.new_position = self.local_param_space.vol_position
        self.__prev_position = self.local_param_space.vol_position
        
        output_file_postfix = f"{self.model.name}_{self.decay}_{global_param_space.mass_string}"

        self.prescan_details_name = os.path.join(self.out_dir,"files","details",f"prescan_details_{output_file_postfix}.txt")
        self.details_name = os.path.join(self.out_dir,"files","details",f"scan_details_{self.__label}_{output_file_postfix}.txt")
        self.walk_file_name = os.path.join(self.out_dir,"files","walk",f"walk_{self.__label}_{output_file_postfix}.tsv")

        # initialize walk file
        with open(self.walk_file_name, "w") as walk_file:
            content = "xb"
            for parameter in initial_pos.parameter_values.keys():
                content += f"\t{parameter}"
            content += "\n"
            walk_file.write(content)

        # copy prescan details file to zoom optimizer details file
        shutil.copy(self.prescan_details_name,self.details_name)

    @property
    def model(self) -> Model:
        """Model used in scan"""
        return self.global_param_space.model

    @property
    def decay(self) -> str:
        """Decay mode used in scan"""
        return self.global_param_space.decay

    @property
    def global_param_space(self) -> ParamSpace:
        """Global param space"""
        return self.__global_param_space
    
    @global_param_space.setter
    def global_param_space(self,
                           new_global_param_space: ParamSpace) -> None:
        """Set the global param space"""
        self.__global_param_space = new_global_param_space

    @property
    def local_param_space(self) -> ParamSpace:
        """Local param space"""
        return self.__local_param_space
    
    @local_param_space.setter
    def local_param_space(self,
                          new_local_param_space: ParamSpace) -> None:
        """Set the local param space"""
        self.__local_param_space = new_local_param_space

    @cached_property
    def out_dir(self) -> str:
        """Output directory name"""
        return scan_dir(model=self.model,
                        decay=self.decay)

    def run(self):

        # get time of mean shift start
        shift_start = time.time()

        # Initialize iteration counter
        iter = -1

        # Initialize counter for number of small steps
        self.n_small_steps = 0

        # Flag to indicate whether iterations should stop
        stop = False

        # Loop until stop condition is met
        while not stop:

            # get time of iteration start
            iter_start = time.time()

            iter += 1

            # get iteration identifier
            identifier = self.__label + f"-{iter:04d}"
            self.logger.info(f"Iteration: {identifier}")

            arrays = None

            # Create scan_parser using the point_sampler class
            try:
                parser = self.point_sampler.sample_points(param_space = self.local_param_space,
                                                          identifier = identifier,
                                                          num_points_requested = self.__points,
                                                          good_points_only = False
                                                         )
            # if point sampling times out, exit
            except TimeoutError:
                self.logger.info(f"No points found. Exiting {identifier}\n")
                return

            arrays = parser.input_parameter_arrays
            xb = parser.get_xb(self.decay)

            if len(xb) == 0:
                #raise ValueError("Length of xb array was 0")
                self.logger.info(f"No points found. Exiting {identifier}\n")
                return

            # Store previous position before calculating a new one
            self.__prev_position = self.new_position

            mean_shift(arrays = arrays,
                       Z = xb,
                       param_space = self.local_param_space)
            
            # get new position
            self.new_position = self.point_sampler.sample_single_point(point=self.local_param_space.vol_position,
                                                                       decay=self.decay,
                                                                       identifier=identifier+"-point")

            stop = self.__stop_check()

            # get iteration end time
            iter_end = time.time()
            iter_time = iter_end - iter_start

            # print iteration time to screen
            self.logger.info(f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n")

            # write scan details to details file
            with open(self.details_name, 'a') as details_file:
                content = f"Iteration = {identifier}\n"
                content += "--------------------\n"
                content += f"Using {self.__points} scan points\n"
                content += "--------------------\n"
                for name in self.local_param_space.parameter_names:
                    content += name + ":\n"
                    content += f"  range = {self.local_param_space[name].format_range()}\n"
                    content += f"  width = {round_sig(self.local_param_space[name].width)}\n"
                content += "--------------------\n"
                content += f"scan_pts  = {self.__points}\n"
                content += f"curr_pos  = {self.new_position}\n"
                content += f"prev_pos  = {self.__prev_position}\n"
                content += f"test_pos  = {self.__test_position}\n"
                content += f"avg_xb    = {round_sig(np.average(xb))}\n"
                content += f"max_xb    = {round_sig(np.max(xb))}\n"
                content += f"new_xb    = {round_sig(self.new_position.xb)}\n"
                content += "--------------------\n"
                content += f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n\n"
                details_file.write(content)

            # NOTE: For debugging
            if self.__debug == True:
                test_diff = tuple([self.__stop_sens_par * w for w in self.local_param_space.vol_width])
                position_diff = tuple([pos[1] - pos[0] for pos in list(zip(self.__prev_position, self.new_position))])

                print(f"small steps = {self.n_small_steps}")
                print(f"avg xb      = {round_sig(np.average(xb))}")
                print(f"max xb      = {round_sig(np.max(xb))}")
                print(f"volume size = {self.local_param_space.vol_width}")
                print(f"curr pos    = {self.local_param_space.vol_position}")
                print(f"prev pos    = {self.__prev_position}")
                print(f"test pos    = {self.__test_position}")
                print(f"reset diff  = {test_diff}")
                print(f"posit diff  = {position_diff}\n")

            # write step details to walk file
            with open(self.walk_file_name, 'a') as walk_file:
                content = f"{round_sig(self.new_position.xb)}"
                for val in self.new_position.parameter_values.values():
                    content += f"\t{round_sig(val)}"
                content += "\n"
                walk_file.write(content)

        # get mean shift end time
        shift_end = time.time()
        shift_time = shift_end - shift_start

        # print iteration time to screen
        self.logger.info(f"{self.__label} took {datetime.timedelta(seconds=int(shift_time))} (hh:mm:ss)\n")

        return

    def __stop_check(self) -> bool:
        """
        If the center point is not moving significantly for a number of iterations,
        return True to signal stopping.
        """
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
