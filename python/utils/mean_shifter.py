import copy
import glob
import random
import sys
import time

from configparser import ConfigParser

import numpy as np

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

    def mean_shift(self, params: dict[np.ndarray], Z: np.ndarray):
        """Updates cente value based on X_1, X_2, ... X_i and Z pairs of a sample volume.

        Args:
            XX (numpy.ndarray[numpy.ndarray(<float>)]): 2D list, each row represents a collection of columns of each dimension.
            Z (numpy.ndarray[<float>]): List of function values for the sample space.

        Returns:
            tuple(x_1, x_2, ... , x_i): The new position tuple of x_1, x_2, ... , x_i coordinates of the distribution.
        """

        XX = ParamMapper(params.keys()).unpack(params)

        nZ = self.lin_norm(Z)

        normalization_factor = np.sum(nZ)

        if normalization_factor == 0.0:
            normalization_factor = sys.float_info.min

        means = []

        for X_i in XX.transpose():
            means.append(np.dot(X_i, nZ) / normalization_factor)

        self.position = tuple(means)

    def extents(self) -> tuple:
        extents = []

        for size, pos in zip(self.size, self.position):
            offset = size / 2

            extents.append((pos - offset, pos + offset))

        return tuple(extents)

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

        # TEST

        return np.vectorize(lambda x: (x - MIN) / (MAX - MIN))(X)
        # return np.array([ ( X[i] - MIN ) / ( MAX - MIN ) for i in range(len(X)) ])

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
            scan_prop: float,
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
        self.__model_name = global_params.model_name()
        self.__decay_name = decay
        self.__label = label
        self.__stop = False
        self.__stop_epochs = stop_epochs
        self.__stop_sens = stop_sens
        self.__max_width = max_width
        self.__epoch_count = 0
        self.__debug = debug

        self.__local_params = copy.deepcopy(global_params)

        super().__init__(
            position=tuple(
                [
                    random.uniform(self.__local_params.get_low(p), self.__local_params.get_high(p))
                    for p in self.__local_params.parnames()
                ]
            ),
            size=tuple(
                [
                    (scan_prop * (self.__local_params.get_high(p) - self.__local_params.get_low(p)))
                    for p in self.__local_params.parnames()
                ]
            ),
        )

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

            num_points = 0
            
            while num_points == 0:
                num_points = runScannerS(
                    ininame=ininame,
                    modelname=self.__model_name,
                    npoints=self.__num_points,
                    use_multiprocessing=use_multiprocessing
                )

                if num_points == 0:
                    print("Warning: ScannerS returned 0 points, retrying")

            save_tsv_output(temptsv, tsvname)
            apply_filters(tsvname, self.__model_name, self.__local_params.masses(), self.__max_width)

            prev_position = self.position

            parser = Parse(self.__local_params.masses(), self.__decay_name, self.__local_params.model_name())
            parser.read_file(tsvname)
            
            arrays = parser.get_parameter_arrays()
            xb = parser.get_xb()

            self.mean_shift(arrays, xb)

            self.__stop_check(prev_position)

            # Add meanshift data to ini file
            with open(ininame, 'a') as file:
                contents = "[meanshift]\n; details about mean shift scan operation (post)"
                contents += f"\niter      = {iter}"
                contents += f"\ncurr_pos  = {' '.join([str(e) for e in self.position])}"
                contents += f"\nprev_pos  = {' '.join([str(e) for e in prev_position])}"
                contents += f"\nst_sens   = {self.__stop_sens}"
                contents += f"\nst_epchs  = {self.__stop_epochs}"
                contents += f"\navg_xb    = {np.average(xb)}"

                file.write(contents)

            self.__generate_visualizations()

            # NOTE: For debugging
            if self.__debug == True:
                change = tuple([pos[1] - pos[0] for pos in list(zip(prev_position, self.position))])
                sens_diff = tuple([self.__stop_sens * p for p in self.position])

                print()
                print(f"iter        = {iter}")
                print()
                print(f"curr pos    = {self.position}")
                print()
                print(f"prev pos    = {prev_position}")
                print()
                print(f"pos change  = {change}")
                print()
                print(f"sens limit  = {sens_diff}")
                print()
                print(f"epoch count = {self.__epoch_count}")

        return self.position

    def __stop_check(self, prev_position: tuple):
        """
        If epoch counter for exceeds max stop epochs then set self.__stop to True.
        """
        advance_epoch = True

        if type(self.__stop_sens) is float:
            for pos, prev in zip(self.position, prev_position):
                percent_difference = np.abs(pos - prev) / prev

                if percent_difference > self.__stop_sens:
                    advance_epoch = False

        if advance_epoch == False:
            self.__epoch_count = 0
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
                    if "iter" in line: ini_data.update({"iter": int(line.split('=')[1])})
                    if "position" in 

                print(ini_data)

                data.append(ini_data)
                

class ParamMapper:

    def __init__(self, param_names: list[str]):
        self.__param_names = [str(param_name) for param_name in param_names]

    def unpack(self, dict: dict) -> np.ndarray:
        if len(dict.keys()) != len(self.__param_names):
            raise ValueError(
                f"Input size size mismatch: {len(dict.keys())}, {len(self.__param_names)}")

        return np.array([dict[key] for key in self.__param_names]).T

    def pack(self, arr: np.ndarray) -> dict:

        if len(arr) != len(self.__param_names):
            raise ValueError(
                f"Input size mismatch: {len(arr)}, {len(self.__param_names)}")

        return {p: a for p, a in zip(self.__param_names, arr)}

    @property
    def param_names(self):
        return self.__param_names
    
    def __str__(self):
        return str(self.__param_names)