import copy
import glob
import operator
import random
import sys
import time

from pprint import pprint

import matplotlib.pyplot as plt
import numpy as np

from scipy.interpolate import interp1d

from filters.filter import apply_filters
from utils.masses import Masses
from parse import Parse
from utils.params import Params, Parameter
from utils.runScannerS import runScannerS
from utils.tsvutils import save_tsv_output


class PointVolume:

    def __init__(self, position: tuple = (0, 0), size: tuple = ((-1, 1), (-1, 1))):
        self._position = position
        self._size = size

    def extents(self) -> tuple:
        extents = []

        for size, pos in zip(self.size, self.position):
            offset = size / 2

            extents.append((pos - offset, pos + offset))

        return tuple(extents)

    @property
    def position(self) -> tuple:
        return self._position

    @property
    def size(self) -> tuple:
        return self._size

    @property
    def stop(self) -> bool:
        return self.__stop

    @position.setter
    def position(self, position: tuple):
        self._position = position

    @size.setter
    def size(self, size: tuple):
        self._size = size

    @stop.setter
    def stop(self, stop: bool):
        self.__stop = stop


class MeanShifter(PointVolume):

    def __init__(
            self,
            files_path: str,
            scan_volume: float,
            stop_mode: int,
            stop_epochs: int,
            stop_sens: float,
            label: str,
            num_points: int,
            decay: str,
            max_width: float,
            global_params: Params,
            debug: bool = False):

        self.__num_points = num_points
        self.__files_path = files_path
        self.__scan_volume = scan_volume
        self.__stop_mode = stop_mode
        self.__model_name = global_params.model_name()
        self.__decay_name = decay
        self.__label = label
        self.__stop = False
        self.__stop_epochs = stop_epochs
        self.__stop_sens = (1 - stop_sens)
        self.__max_width = max_width
        self.__epoch_count = 0
        self.__debug = debug

        self.__local_params = copy.deepcopy(global_params)

        super().__init__(
            position=self.__get_random_pos(),
            size=self.__get_size(),
            debug=self.__debug
        )

        self.__test_position = self.position
        self.__prev_position = self.position

        for (parname, extents) in list(zip(self.__local_params.parnames(), self.extents())):
            self.__local_params.parameter(parname).set_low(extents[0])
            self.__local_params.parameter(parname).set_high(extents[1])

    def run(self, use_multiprocessing: bool):
        # get time of iteration start
        iterstart = time.time()

        iter = -1

        while self.__stop != True:
            iter += 1

            # get iteration identifier
            identifier = self.__label + f"-{iter:04d}"
            print("\nIteration:", identifier)

            # set names of input .ini and output .tsv files
            outname = self.__files_path + "files/" + self.__model_name + "_" + identifier
            ininame = outname + ".ini"
            tsvname = outname + ".tsv"
            temptsv = self.__files_path + self.__model_name + ".tsv"

            # write new .ini file from template and parameters
            self.__local_params.write_ini(ininame)

            parser = None
            arrays = None
            xb = []

            runScannerS(
                ininame=ininame,
                modelname=self.__model_name,
                npoints=self.__num_points,
                use_multiprocessing=use_multiprocessing
            )

            save_tsv_output(temptsv, tsvname)

            try:
                apply_filters(tsvname, self.__model_name, self.__local_params.masses(), self.__max_width)

                parser = Parse(self.__local_params.masses(), self.__decay_name, self.__local_params.model_name())
                parser.read_file(tsvname)

                arrays = parser.get_parameter_arrays()
                xb = parser.get_xb()

                if len(xb) == 0:
                    raise ValueError("Length of xb array was 0")
            except Exception as e:
                print(e)
                print("\nError parsing tsv output, stopping execution...\n")
                exit(1)

            self.__prev_position = self.position

            self.mean_shift(arrays, xb)
            
            # Update params
            for (parname, extents) in list(zip(self.__local_params.parnames(), self.extents())):
                self.__local_params.parameter(parname).set_low(extents[0])
                self.__local_params.parameter(parname).set_high(extents[1])
            
            self.__stop_check()

            # Add meanshift data to ini file
            with open(ininame, 'a') as file:
                contents = "[meanshift result]\n; details about mean shift scan operation (post)"
                contents += f"\niter      = {iter}"
                contents += f"\nnum pts   = {self.__num_points}"
                contents += f"\nscan vol  = {self.__scan_volume}"
                contents += f"\ncurr_pos  = {' '.join([str(p) for p in self.position])}"
                contents += f"\nprev_pos  = {' '.join([str(p) for p in self.__prev_position])}"
                contents += f"\ntest_pos  = {' '.join([str(p) for p in self.__test_position])}"
                contents += f"\nvol_size  = {' '.join([str(p) for p in self.size])}"
                contents += f"\nst_sens   = {self.__stop_sens}"
                contents += f"\nst_epchs  = {self.__stop_epochs}"
                contents += f"\ncur_epch  = {self.__epoch_count}"
                contents += f"\navg_xb    = {np.average(xb)}"
                contents += f"\nmax_xb    = {np.max(xb)}"

                file.write(contents)

            # NOTE: For debugging
            if self.__debug == True:
                test_diff = tuple([self.__stop_sens * dimen for dimen in self.size])
                position_diff = tuple([pos[1] - pos[0] for pos in list(zip(self.__prev_position, self.position))])

                print()
                print(f"iter        = {iter}")
                print(f"num points  = {self.__num_points}")
                print(f"scan vol    = {self.__scan_volume}")
                print(f"stop mode   = {'test pt' if self.__stop_mode == 0 else 'prev pt'}")
                print(f"stop sens % = {self.__stop_sens}")
                print(f"stop epochs = {self.__stop_epochs}")
                print(f"epoch count = {self.__epoch_count}")
                print(f"avg xb      = {np.average(xb)}")
                print(f"max xb      = {np.max(xb)}")
                print()
                print(f"volume size = {self.size}")
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

    def __get_random_pos(self):
        return tuple(
            [
                random.uniform(self.__local_params.get_low(p), self.__local_params.get_high(p))
                for p in self.__local_params.parnames()
            ]
        )

    def __get_size(self):
        return tuple(
            [
                (self.__scan_volume * (self.__local_params.get_high(p) - self.__local_params.get_low(p)))
                for p in self.__local_params.parnames()
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

    def __generate_visualizations(self):
        ini_files = glob.glob(self.__files_path + "files/" + self.__local_params.model_name() + "*.ini")

        data = []

        for path in ini_files:
            with open(path, 'r') as file:
                ini_data = dict()

                for line in file:
                    if "iter" in line:
                        ini_data.update({"iter": int(line.strip().split('=')[1])})
                    if "vol_size" in line:
                        ini_data.update({"vol_size": {
                            p: a for p, a in zip(
                                self.__local_params.parnames(),
                                [float(token) for token in line.split('=')[1].strip().split(' ')]
                            )}
                        })
                    if "curr_pos" in line:
                        ini_data.update({"curr_pos": {
                            p: a for p, a in zip(
                                self.__local_params.parnames(),
                                [float(token) for token in line.split('=')[1].strip().split(' ')]
                            )}
                        })
                    if "prev_pos" in line:
                        ini_data.update({"prev_pos": {
                            p: a for p, a in zip(
                                self.__local_params.parnames(),
                                [float(token) for token in line.split('=')[1].strip().split(' ')]
                            )}
                        })
                    if "test_pos" in line:
                        ini_data.update({"test_pos": {
                            p: a for p, a in zip(
                                self.__local_params.parnames(),
                                [float(token) for token in line.split('=')[1].strip().split(' ')]
                            )}
                        })
                    if "avg_xb" in line:
                        ini_data.update({"avg_xb": float(line.strip().split('=')[1])})
                    if "max_xb" in line:
                        ini_data.update({"max_xb": float(line.strip().split('=')[1])})

                data.append(copy.deepcopy(ini_data))

        data_sorted = sorted(data, key=operator.itemgetter("iter"))

        if self.__debug == True:
            print()
            print("Arrays sorted\n========")
            for d in data_sorted:
                pprint(d, sort_dicts=False)
            print()

        # Create scatter plot
        for i in range(len(self.__local_params.parnames())):
            for j in range(i, len(self.__local_params.parnames())):
                x_label = self.__local_params.parnames()[i]
                y_label = self.__local_params.parnames()[j]

                X = []
                Y = []

                for datum in data_sorted:
                    X.append(datum["curr_pos"][x_label])
                    Y.append(datum["curr_pos"][y_label])

                for k, (x, y) in enumerate(list(zip(X, Y))):
                    plt.plot(x, y, marker='*' if k == (len(X) - 1) else '.')
                    plt.annotate(str(k), (x, y))

                plt.xlabel(x_label)
                plt.ylabel(y_label)
                plt.savefig(f"{self.__files_path}files/{self.__local_params.model_name()}_scatter_{x_label}_{y_label}.jpg", format="JPEG")
                plt.cla()
                plt.clf()

        # Create lines plot
        for i in range(len(self.__local_params.parnames())):
            for j in range(i, len(self.__local_params.parnames())):
                x_label = self.__local_params.parnames()[i]
                y_label = self.__local_params.parnames()[j]

                X = []
                Y = []

                for datum in data_sorted:
                    X.append(datum["curr_pos"][x_label])
                    Y.append(datum["curr_pos"][y_label])

                plt.plot(X, Y)
                plt.plot(X[len(X) - 1], Y[len(Y) - 1], marker="*")

                plt.xlabel(x_label)
                plt.ylabel(y_label)
                # plt.scatter(X, Y)
                plt.savefig(f"{self.__files_path}files/{self.__local_params.model_name()}_lines_{x_label}_{y_label}.jpg", format="JPEG")
                plt.cla()
                plt.clf()

        # Create time series
        for parname in self.__local_params.parnames():
            X = []
            Y = []
            avg_xb = []
            max_xb = []

            for datum in data_sorted:

                X.append(datum["iter"])
                Y.append(datum["curr_pos"][parname])
                avg_xb.append(datum["avg_xb"])
                max_xb.append(datum["max_xb"])

            avg_xb_range = [min(avg_xb), max(avg_xb)]
            max_xb_range = [min(max_xb), max(max_xb)]
            y_range = [min(Y), max(Y)]
            avg_xb_interpolator = interp1d(avg_xb_range, y_range)
            max_xb_interpolator = interp1d(max_xb_range, y_range)

            plt.plot(X, [max_xb_interpolator(elem) for elem in max_xb], c="tab:red", label="max xb")
            plt.plot(X, [avg_xb_interpolator(elem) for elem in avg_xb], c="tab:orange", label="average xb")
            plt.plot(X, Y, c="tab:blue", label=parname)
            plt.legend(loc="lower right")
            plt.xlabel("iter")
            plt.ylabel(parname)
            plt.savefig(f"{self.__files_path}files/{self.__local_params.model_name()}_timeseries_iter_xb({parname}).jpg", format="JPEG")
            plt.cla()
            plt.clf()
