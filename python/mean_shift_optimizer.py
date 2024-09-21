
import copy
import datetime
import glob
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

from filters.filter import apply_filters
from parse import Parse
from utils.params import Params, Parameter
from utils.runScannerS import runScannerS
from utils.tsvutils import save_tsv_output
from utils.config_loader import ConfigLoader

class PointVolume:

    def __init__(self, position: tuple = (0, 0), widths: tuple = ((-1, 1), (-1, 1))):
        self._position = position
        self._widths = widths

    def extents(self) -> tuple:
        extents = []

        for width, pos in zip(self.width, self.position):
            offset = width / 2

            extents.append((pos - offset, pos + offset))

        return tuple(extents)

    @property
    def position(self) -> tuple:
        return self._position

    @property
    def width(self) -> tuple:
        return self._widths

    @property
    def stop(self) -> bool:
        return self.__stop

    @position.setter
    def position(self, position: tuple):
        self._position = position

    @width.setter
    def width(self, width: tuple):
        self._widths = width

    @stop.setter
    def stop(self, stop: bool):
        self.__stop = stop


class MeanShiftOptimizer(PointVolume):

    def __init__(
            self,
            scan_path: str,
            plot_path: str,
            scan_volume: float,
            stop_mode: int,
            stop_epochs: int,
            stop_sens: float,
            label: str,
            initial_pos: tuple[tuple],
            num_points: int,
            decay: str,
            global_params: Params,
            config_loader: ConfigLoader,
            debug: bool = False):

        self.__num_points = num_points
        self.__scan_path = scan_path
        self.__plot_path = plot_path
        self.__model_name = global_params.model_name()
        self.__decay_name = decay
        self.__label = label
        self.__scan_volume = scan_volume
        self.__stop_epochs = stop_epochs
        self.__stop_mode = stop_mode
        self.__stop_sens = (1 - stop_sens)

        self.__config_loader = config_loader
        self.__debug = debug

        self.__epoch_count = 0
        self.__stop = False

        self.__local_params = copy.deepcopy(global_params)

        super().__init__(
            position=initial_pos,
            widths=self.__get_widths()
        )

        self.__test_position = self.position
        self.__prev_position = self.position

        for i, param in enumerate(self.__local_params):
            param.set_low(self.extents()[i][0])
            param.set_high(self.extents()[i][1])

    def run(self, use_multiprocessing: bool):
        num_points = self.__num_points
        scan_volume = self.__scan_volume
        decay_name = self.__decay_name
        model_name = self.__model_name
        local_params = self.__local_params
        config_loader = self.__config_loader
        stop_sens = self.__stop_sens
        stop_epochs = self.__stop_epochs
        stop_mode = self.__stop_mode
        debug = self.__debug

        # get time of iteration start
        iterstart = time.time()

        iter = -1

        while self.__stop != True:
            iter += 1

            # get iteration identifier
            identifier = self.__label + f"-{iter:04d}"
            print("\nIteration:", identifier)

            # set names of input .ini and output .tsv files
            outpath = f"{self.__scan_path}files/{self.__model_name}_{identifier}"
            log_file_name = outpath + identifier + "_log.txt"
            ininame = outpath + ".ini"
            tsvname = outpath + ".tsv"
            temptsv = self.__scan_path + self.__model_name + ".tsv"
            detailsname = f"{self.__scan_path}scandetails_{self.__model_name}_{self.__decay_name}_{str(self.__local_params.masses())}.txt"

            # write new .ini file from template and parameters
            self.__local_params.write_ini(ininame)

            parser = None
            arrays = None
            xb = []

            runScannerS(
                ini_name=ininame,
                num_points=self.__num_points,
                model_name=self.__model_name,
                use_multiprocessing=use_multiprocessing
            )

            save_tsv_output(temptsv, tsvname)

            nwidth = None
            nbounds = None
            npass = None

            nwidth, nbounds, nsignals, npass = apply_filters(
                file_name=tsvname,
                masses=local_params.masses(),
                config_loader=config_loader
            )

            parser = Parse(
                masses=local_params.masses(),
                model_name=model_name,
                file_name=tsvname
            )

            arrays = parser.get_parameter_arrays()
            xb = parser.get_xb(decay_name)

            if len(xb) == 0:
                raise ValueError("Length of xb array was 0")
                
            self.__prev_position = self.position

            self.mean_shift(arrays, xb)

            # Update params
            for i, param in enumerate(local_params):
                param.set_low(self.extents()[i][0])
                param.set_high(self.extents()[i][1])

            self.__stop_check()

            # get iteration end time
            iterend = time.time()
            itertime = iterend - iterstart

            # print iteration time to screen
            print(f"Iteration took {datetime.timedelta(seconds=int(itertime))} (hh:mm:ss)")

            # write shift log
            log_file = open(log_file_name, 'w')
            content = f"\niter      = {iter}"
            content += f"\nnum pts   = {num_points}"
            content += f"\nscan vol  = {scan_volume}"
            content += f"\ncurr_pos  = {' '.join([str(p) for p in self.position])}"
            content += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
            content += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
            content += f"\nvol_widths  = {' '.join([str(p) for p in self.width])}"
            content += f"\nst_sens   = {stop_sens}"
            content += f"\nst_epchs  = {stop_epochs}"
            content += f"\ncur_epch  = {self.__epoch_count}"
            content += f"\navg_xb    = {np.average(xb)}"
            content += f"\nmax_xb    = {np.max(xb)}"
            log_file.write(content)
            log_file.close()

            # write scan details to details file
            details_file = open(detailsname, 'a')
            content = f"Iteration = {identifier}\n"
            content += "--------------------\n"
            content += f"Using {num_points} scan points\n"
            content += f"{nbounds}/{num_points} pass bounds check\n"
            content += str(nsignals) + "/" + str(self.__num_points) + " pass signals check\n"
            content += f"{npass}/{num_points} pass both checks\n"
            # content += "--------------------\n"
            # content += "Found new max xsec*BR = " + newPoint.format_xb() + "\n"
            # content += "Update optimal point: " + str(update) + "\n"
            # content += "Optimal point xsec*BR = " + self.optPoint.format_xb() + "\n"
            content += "--------------------\n"
            for name in local_params.parameter_names():
                content += name + ":\n"
                content += f"  {local_params[name].format_range()}\n"
            content += "--------------------\n"
            content += f"iter      = {iter}"
            content += f"\nnum pts   = {num_points}"
            content += f"\nscan vol  = {scan_volume}"
            content += f"\ncols      = {' '.join(local_params.parameter_names())}"
            content += f"\ncurr_pos  = {' '.join([str(p) for p in self.position])}"
            content += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
            content += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
            content += f"\nvol_widths  = {' '.join([str(p) for p in self.width])}"
            content += f"\nst_sens   = {stop_sens}"
            content += f"\nst_epchs  = {stop_epochs}"
            content += f"\ncur_epch  = {self.__epoch_count}"
            content += f"\navg_xb    = {np.average(xb)}"
            content += f"\nmax_xb    = {np.max(xb)}\n"
            content += "--------------------\n"
            content += f"Iteration took {datetime.timedelta(seconds=int(itertime))} (hh:mm:ss)\n"
            content += "\n\n"
            details_file.write(content)
            details_file.close()

            # NOTE: For debugging
            if debug == True:
                test_diff = tuple([stop_sens * dimen for dimen in self.width])
                position_diff = tuple([pos[1] - pos[0] for pos in list(zip(self.__prev_position, self.position))])

                print()
                print(f"iter        = {iter}")
                print(f"num points  = {num_points}")
                print(f"scan vol    = {scan_volume}")
                print(f"stop mode   = {'test pt' if stop_mode == 0 else 'prev pt'}")
                print(f"stop sens % = {stop_sens}")
                print(f"stop epochs = {stop_epochs}")
                print(f"epoch count = {self.__epoch_count}")
                print(f"avg xb      = {np.average(xb)}")
                print(f"max xb      = {np.max(xb)}")
                print()
                print(f"volume size = {self.width}")
                print()
                print(f"curr pos    = {self.position}")
                print()
                print(f"prev pos    = {self.__prev_position}")
                print()
                print(f"test pos    = {self.__test_position}")
                print()
                print(f"reset diff  = {test_diff}")
                print()
                print(f"posit diff  = {position_diff}")

        self.__create_data_file()
        self.__generate_visualizations()

        return self.position

    def mean_shift(self, params: dict[np.ndarray], Z: np.ndarray):
        """Updates cente value based on X_1, X_2, ... X_i and Z pairs of a sample volume.

        Args:
            XX (dict[numpy.ndarray(<float>)]): 2D list, each row represents a collection of columns of each dimension.
            Z (numpy.ndarray[<float>]): List of function values for the sample space.

        Returns:
            tuple(x_1, x_2, ... , x_i): The new position tuple of x_1, x_2, ... , x_i coordinates of the distribution.
        """

        XX = np.array([params[key] for key in params])

        nZ = self.lin_norm(Z)

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

        self.position = tuple(means)

    @staticmethod
    def lin_norm(X: list):
        """Linear normalization of X

        Args:
            X (list[<float>]): List of values to normalize.

        Returns:
            (list[<float>]): A normalized list of the values contained in the input list.
        """
        MAX = max(X)
        MIN = min(X)

        return np.array([(X[i] - MIN) / (MAX - MIN) for i in range(len(X))])

    def __get_widths(self):
        return tuple(
            [
                (self.__scan_volume * (self.__local_params[name].get_high() - self.__local_params[name].get_low()))
                for name in self.__local_params.parameter_names()
            ]
        )

    def __stop_check(self):
        """
        If epoch counter for exceeds max stop epochs then set self.__stop to True.
        """
        advance_epoch = True

        for pos, test in zip(self.position, self.__test_position if self.__stop_mode == 0 else self.__prev_position):
            percent_difference = np.abs(pos - test) / test

            if percent_difference > self.__stop_sens:
                advance_epoch = False

        if advance_epoch == False:
            self.__epoch_count = 0
            self.__test_position = self.position
        else:
            self.__epoch_count += 1

        if (self.__epoch_count >= self.__stop_epochs):
            self.__stop = True

    def __create_data_file(self):
        files = glob.glob(f"{self.__scan_path}files/{self.__local_params.model_name()}*_log.txt")
        
        data_file_path = f"{self.__scan_path}files/meanshift_walk.tsv"

        data = []

        for path in files:
            with open(path, 'r') as file:
                elem = dict()

                for line in file:
                    if "iter" in line:
                        elem.update({"iter": int(line.strip().split('=')[1])})
                    if "vol_widths" in line:
                        elem.update(
                            {
                                f"vol_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names(),
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "curr_pos" in line:
                        elem.update(
                            {
                                p: a for p, a in zip(
                                    self.__local_params.parameter_names(),
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "prev_pos" in line:
                        elem.update(
                            {
                                f"prev_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names(),
                                    [float(token) for token in line.split('=')[1].strip().split(' ')]
                                )
                            }
                        )
                    if "test_pos" in line:
                        elem.update(
                            {
                                f"test_{p}": a for p, a in zip(
                                    self.__local_params.parameter_names(),
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
        df.to_csv(data_file_path, sep="\t")

    def __generate_visualizations(self):
        # Create plots dir
        os.makedirs(self.__plot_path, exist_ok=True)

        data_file_path = f"{self.__scan_path}files/meanshift_walk.tsv"

        df = pd.read_csv(data_file_path, sep="\t")

        # Create param plots
        for i in range(len(self.__local_params.parameter_names())):
            for j in range(i, len(self.__local_params.parameter_names())):
                x_label = self.__local_params.parameter_names()[i]
                y_label = self.__local_params.parameter_names()[j]

                plt.plot(df[x_label], df[y_label])
                plt.plot(df[x_label].iloc[-1], df[y_label].iloc[-1], marker="*")

                plt.xlabel(x_label)
                plt.ylabel(y_label)
                # plt.scatter(X, Y)
                plt.savefig(f"{self.__plot_path}{self.__local_params.model_name()}_lines_{x_label}_{y_label}.jpg", format="JPEG")
                plt.cla()
                plt.clf()

        # Create time series
        for parname in self.__local_params.parameter_names():
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
            plt.savefig(f"{self.__plot_path}{self.__local_params.model_name()}_timeseries_iter_{parname}_xb.jpg", format="JPEG")
            plt.cla()
            plt.clf()
