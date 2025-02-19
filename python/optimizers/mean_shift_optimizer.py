#!/usr/bin/env python3

import copy
import datetime
import glob
import logging
import operator
import os
import sys
import time

from pprint import pprint

import matplotlib
import matplotlib.lines
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

from utils import file_utils

from utils.params import Params
from utils.config_loader import ConfigLoader
from utils.point_sampler import PointSampler
from utils.mean_shift_utils import lin_norm

class MeanShiftOptimizer:

    def __init__(
            self,
            scan_perc: float,
            stop_mode: int,
            stop_epochs: int,
            stop_sens: float,
            label: str,
            initial_pos: tuple[tuple],
            points: int,
            global_params: Params,
            config_loader: ConfigLoader,
            debug: bool = False):
        
        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        self.__points = points
        self.__label = label
        self.__scan_percentage = scan_perc
        self.__stop_epochs = stop_epochs
        self.__stop_mode = stop_mode
        self.__stop_sens = (1 - stop_sens)
        self.__model = global_params.model
        self.__decay_name = global_params.decay

        # Initialize paths
        self.__scan_path = file_utils.scan_dir(
                self.__model,
                self.__decay_name
            )
        
        self.__plot_path = file_utils.plots_dir(
                self.__model,
                self.__decay_name
            )

        # Initialize config loader
        self.__config_loader = config_loader
        self.__debug = debug

        # Initialize control variables for iteration
        self.__epoch_count = 0
        self.__stop = False

        # Copy of params so that multiple instances of ms use global params
        self.__local_params = copy.deepcopy(global_params)

        # Set initial param widths
        for param in self.__local_params:
            center = param.center
            extent = (param.width * scan_perc) / 2

            param.low = (center - extent)
            param.high = (center + extent)

        # Set center of new params
        self.__local_params.reposition_center(initial_pos)

        # Initialize positions
        self.__test_position = self.__local_params.vol_position
        self.__prev_position = self.__local_params.vol_position

        # Init point sampler
        self.point_sampler = PointSampler(out_dir = self.__scan_path,
                                        config_loader = self.__config_loader,
                                        use_file_dir = True)

    def run(self):
        # make log file directory
        os.makedirs(f"{self.__scan_path}files/log/", exist_ok=True)

        # get time of iteration start
        iter_start = time.time()

        # log initial state
        log_file = open(f"{self.__scan_path}files/log/{self.__model.name}_{self.__label}-init_log.txt", 'w')
        content = f"\niteration  = -1"
        content += f"\nscan_pts  = {self.__points}"
        content += f"\nlabel     = {self.__label}"
        content += f"\nscan_perc = {self.__scan_percentage}"
        content += f"\ncurr_pos  = {' '.join([str(p) for p in self.__local_params.vol_position])}"
        content += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
        content += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
        content += f"\nwidths    = {' '.join([str(p) for p in self.__local_params.vol_width])}"
        content += f"\nstop_sens = {self.__stop_sens}"
        content += f"\nstop_epochs= {self.__stop_epochs}"
        content += f"\ncurr_epoch = {self.__epoch_count}"
        log_file.write(content)
        log_file.close()

        # Initialize iteration counter
        iter = -1

        # Loop until stop condition is met
        while self.__stop != True:
            iter += 1

            # get iteration identifier
            identifier = self.__label + f"-i{iter:04d}"
            self.logger.info(f"Iteration: {identifier}")

            # set names of input .ini and output .tsv files
            outpath = f"{self.__scan_path}files/"
            log_file_name = f"{self.__scan_path}files/log/{self.__model.name}_{identifier}_log.txt"
            ininame = outpath + f"/ini/{self.__model.name}_{identifier}.ini"
            details_name = f"{self.__scan_path}scandetails_{self.__model.name}_{self.__decay_name}_{str(self.__local_params.mass_string)}.txt"

            # write new .ini file from template and parameters
            self.__local_params.write_ini(ininame)

            parser = None
            arrays = None

            # Create scan_parser using the point_sampler class
            parser = self.point_sampler.sample_points(params = self.__local_params,
                                                                identifier = identifier,
                                                                num_points_requested = self.__points,
                                                                good_points_only = True
                                                                )

            arrays = parser.input_parameter_arrays
            xb = parser.get_xb(self.__decay_name)

            if len(xb) == 0:
                raise ValueError("Length of xb array was 0")
                
            self.__prev_position = self.__local_params.vol_position

            self.mean_shift(arrays, xb)

            self.__stop_check()

            # get iteration end time
            iter_end = time.time()
            iter_time = iter_end - iter_start

            # print iteration time to screen
            self.logger.info(f"Iteration took {datetime.timedelta(seconds=int(iter_time))} (hh:mm:ss)\n")

            # write shift log
            log_file = open(log_file_name, 'w')
            content = f"\niteration  = {iter}"
            content += f"\nscan_pts  = {self.__points}"
            content += f"\nlabel     = {self.__label}"
            content += f"\nscan_perc = {self.__scan_percentage}"
            content += f"\ncurr_pos  = {' '.join([str(p) for p in self.__local_params.vol_position])}"
            content += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
            content += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
            content += f"\nwidths    = {' '.join([str(p) for p in self.__local_params.vol_width])}"
            content += f"\nstop_sens = {self.__stop_sens}"
            content += f"\nstop_epochs= {self.__stop_epochs}"
            content += f"\ncurr_epoch = {self.__epoch_count}"
            content += f"\navg_xb    = {np.average(xb)}"
            content += f"\nmax_xb    = {np.max(xb)}"
            log_file.write(content)
            log_file.close()

            # write scan details to details file
            details_file = open(details_name, 'a')
            content = f"Iteration = {identifier}\n"
            content += "--------------------\n"
            content += f"Using {self.__points} scan points\n"
            # content += "--------------------\n"
            # content += "Found new max xsec*BR = " + newPoint.format_xb() + "\n"
            # content += "Update optimal point: " + str(update) + "\n"
            # content += "Optimal point xsec*BR = " + self.optPoint.format_xb() + "\n"
            content += "--------------------\n"
            for name in self.__local_params.parameter_names:
                content += name + ":\n"
                content += f"  {self.__local_params[name].format_range()}\n"
            content += "--------------------\n"
            content += f"iteration   = {iter}"
            content += f"\nscan_pts  = {self.__points}"
            content += f"\nlabel     = {self.__label}"
            content += f"\nscan_perc = {self.__scan_percentage}"
            content += f"\ncols      = {' '.join(self.__local_params.parameter_names)}"
            content += f"\ncurr_pos  = {' '.join([str(p) for p in self.__local_params.vol_position])}"
            content += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
            content += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
            content += f"\nwidths    = {' '.join([str(width) for width in self.__local_params.vol_width])}"
            content += f"\nstop_sens = {self.__stop_sens}"
            content += f"\nstop_epchs= {self.__stop_epochs}"
            content += f"\ncurr_epch = {self.__epoch_count}"
            content += f"\navg_xb    = {np.average(xb)}"
            content += f"\nmax_xb    = {np.max(xb)}\n"
            content += "--------------------\n"
            content += f"Iteration took {iter_end - iter_start}\n"
            content += "\n\n"
            details_file.write(content)
            details_file.close()

            # NOTE: For debugging
            if self.__debug == True:
                test_diff = tuple([self.__stop_sens * w for w in self.__local_params.vol_width])
                position_diff = tuple([pos[1] - pos[0] for pos in list(zip(self.__prev_position, self.__local_params.vol_position))])

                print()
                print(f"iter        = {iter}")
                print(f"scan points = {self.__points}")
                print(f"scan %      = {self.__scan_percentage}")
                print(f"stop mode   = {'test pt' if self.__stop_mode == 0 else 'prev pt'}")
                print(f"stop sens % = {self.__stop_sens}")
                print(f"stop epochs = {self.__stop_epochs}")
                print(f"epoch count = {self.__epoch_count}")
                print(f"avg xb      = {np.average(xb)}")
                print(f"max xb      = {np.max(xb)}")
                print()
                print(f"volume size = {self.__local_params.vol_width}")
                print()
                print(f"curr pos    = {self.__local_params.vol_position}")
                print()
                print(f"prev pos    = {self.__prev_position}")
                print()
                print(f"test pos    = {self.__test_position}")
                print()
                print(f"reset diff  = {test_diff}")
                print()
                print(f"posit diff  = {position_diff}")

        self.__create_walk_file()
        self.__generate_visualizations()

        return self.__local_params.center_points()

    def mean_shift(self, params: dict[np.ndarray], Z: np.ndarray):
        """Updates center value based on X_1, X_2, ... X_i and Z pairs of a sample volume.

        Args:
            XX (dict[numpy.ndarray(<float>)]): 2D list, each row represents a collection of columns of each dimension.
            Z (numpy.ndarray[<float>]): List of function values for the sample space.

        Returns:
            tuple(x_1, x_2, ... , x_i): The new position tuple of x_1, x_2, ... , x_i coordinates of the distribution.
        """

        XX = np.array([params[key] for key in params])

        nZ = lin_norm(Z)

        if self.__debug == True:
            print("\nPre-shift:\n========")
            for i, X in enumerate(XX):
                print(f"X_{i}:")
                print(X)
            print("nZ")
            print(nZ)

        normalization_factor = np.sum(nZ)

        if normalization_factor == 0.0:
            normalization_factor = sys.float_info.min

        means = []

        for X_i in XX:
            means.append(np.dot(X_i, nZ) / normalization_factor)

        self.__local_params.reposition_center(tuple(means))

    def __stop_check(self):
        """
        If epoch counter for exceeds max stop epochs then set self.__stop to True.
        """
        advance_epoch = True

        for pos, test in zip(self.__local_params.center_points(), self.__test_position if self.__stop_mode == 0 else self.__prev_position):
            percent_difference = np.abs(pos - test) / test

            if percent_difference > self.__stop_sens:
                advance_epoch = False

        if advance_epoch == False:
            self.__epoch_count = 0
            self.__test_position = self.__local_params.vol_position
        else:
            self.__epoch_count += 1

        if (self.__epoch_count >= self.__stop_epochs):
            self.__stop = True

    def __create_walk_file(self):
        log_files = glob.glob(f"{self.__scan_path}files/log/*{self.__label}*_log.txt")
        
        walk_tsv = f"{self.__scan_path}files/tsv/{self.__label}_meanshift_walk.tsv"

        data = []

        for path in log_files:
            with open(path, 'r') as file:
                elem = dict()

                for line in file:
                    if "iter" in line:
                        elem.update({"iter": int(line.strip().split('=')[1])})
                    if "widths" in line:
                        elem.update(
                            {
                                f"vol_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names,
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "curr_pos" in line:
                        elem.update(
                            {
                                p: a for p, a in zip(
                                    self.__local_params.parameter_names,
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "prev_pos" in line:
                        elem.update(
                            {
                                f"prev_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names,
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "test_pos" in line:
                        elem.update(
                            {
                                f"test_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names,
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "avg_xb" in line:
                        elem.update({"avg_xb": float(line.strip().split('=')[1])})
                    if "max_xb" in line:
                        elem.update({"max_xb": float(line.strip().split('=')[1])})

                data.append(copy.deepcopy(elem))

        data_sorted = sorted(data, key=operator.itemgetter("iter"))

        if self.__debug == True:
            print()
            print("Data sorted\n========")
            for d in data_sorted:
                pprint(d, sort_dicts=False)
            print()

        df = pd.DataFrame(data_sorted)
        df.to_csv(walk_tsv, sep="\t")

    def __generate_visualizations(self):
        # Create plots dir
        os.makedirs(self.__plot_path, exist_ok=True)

        walk_tsv = f"{self.__scan_path}files/tsv/{self.__label}_meanshift_walk.tsv"

        df = pd.read_csv(walk_tsv, sep="\t")

        # Create param plots
        for i in range(len(self.__local_params.parameter_names)):
            for j in range(i, len(self.__local_params.parameter_names)):
                x_label = self.__local_params.parameter_names[i]
                y_label = self.__local_params.parameter_names[j]

                plt.plot(df[x_label], df[y_label])
                plt.plot(df[x_label].iloc[-1], df[y_label].iloc[-1], marker="*")

                plt.xlabel(x_label)
                plt.ylabel(y_label)
                # plt.scatter(X, Y)
                plt.savefig(f"{self.__plot_path}{self.__local_params.model_name}_lines_{self.__label}_{x_label}_{y_label}.jpg", format="JPEG")
                plt.cla()
                plt.clf()

        # Create time series
        for parname in self.__local_params.parameter_names:
            plt.plot(df["iter"], df[parname], c="tab:blue", label=parname)
            plt.xlabel("iter")
            plt.ylabel(parname)
            ax2 = plt.gca().twinx()
            ax2.plot(df["iter"], df["max_xb"], c="tab:red", label="max xb")
            ax2.plot(df["iter"], df["avg_xb"], c="tab:orange", label="average xb")
            ax2.set_ylabel("xb")
            param_man = matplotlib.lines.Line2D([0], [0], c="tab:blue", label=parname)
            handles, labels = plt.gca().get_legend_handles_labels()
            handles.extend([param_man])
            labels.extend([parname])
            handles.reverse()
            labels.reverse()
            plt.legend(handles = handles, labels = labels, loc = "lower right", )
            plt.savefig(f"{self.__plot_path}{self.__local_params.model_name}_timeseries_iter_{self.__label}_{parname}_xb.jpg", format="JPEG")
            plt.cla()
            plt.clf()