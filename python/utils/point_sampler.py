#!/usr/bin/env python3

# standard libraries
import logging
import math

# local modules
from filters.filter import apply_filters
from utils.config_loader import ConfigLoader
from utils.param_space import ParamSpace
from utils.parse import Parse
from utils.point import Point
from utils.run_scannerS import run_scannerS, run_scannerS_single_point
from utils.tsv_utils import save_tsv_output

class PointSampler:

    # Initializer: passes output directory, model name, and config loader
    def __init__(self,
                 out_dir: str,
                 config_loader: ConfigLoader,
                 use_file_dir: bool = False) -> None:

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize class variables
        self.out_dir = out_dir
        self.ini_dir = out_dir
        self.tsv_dir = out_dir
        if use_file_dir:
            self.ini_dir += "files/ini/"
            self.tsv_dir += "files/tsv/"
        self.config_loader = config_loader
        self.efficiency = 1.0

    @property
    def nwidth(self) -> int:
        """Number of points passing width check"""
        return self.__nwidth

    @nwidth.setter
    def nwidth(self,
               new_n_width: int) -> None:
        """Sets number of points passing width check"""
        self.__nwidth = new_n_width

    @property
    def nbounds(self) -> int:
        """Number of points passing bounds check"""
        return self.__nbounds

    @nbounds.setter
    def nbounds(self,
                new_n_bounds: int) -> None:
        """Sets number of points passing bounds check"""
        self.__nbounds = new_n_bounds

    @property
    def nsignals(self) -> int:
        """Number of points passing signals check"""
        return self.__nsignals

    @nsignals.setter
    def nsignals(self,
                 new_n_signals: int) -> None:
        """Sets number of points passing signals check"""
        self.__nsignals = new_n_signals

    @property
    def npass(self) -> int:
        """Number of points passing all checks"""
        return self.__npass

    @npass.setter
    def npass(self,
              new_n_pass: int) -> None:
        """Sets number of points passing all checks"""
        self.__npass = new_n_pass

    @property
    def total_points_run(self) -> int:
        """Number of points that have been run"""
        return self.curr_points_run

    # Method to sample a number of points
    def sample_points(self,
                      param_space: ParamSpace,
                      num_points_requested: int,
                      identifier = "",
                      good_points_only: bool = False) -> Parse:

        # Set names of input .ini and output .tsv files
        out_name = param_space.model_name
        # Check if identifier is defined
        if identifier:
            out_name += "_" + identifier
        ini_name = self.ini_dir + out_name + ".ini"
        tsv_name = self.tsv_dir + out_name + ".tsv"
        temp_tsv = self.out_dir + param_space.model_name + ".tsv"

        # Global variable for number of points
        self.total_points_requested = num_points_requested

        # Write new .ini file from template and parameters
        param_space.write_ini(ini_name)

        # Initialize parser
        self.parser = Parse(param_space.model)

        # Initialize filter counters
        self.nwidth = 0
        self.nbounds = 0
        self.nsignals = 0
        self.npass = 0

        # Initialize the amount of points run
        self.curr_points_run = 0

        # Print total number of points requested
        self.logger.info(f"{self.total_points_requested} points requested")

        # Run until points passed is >= points asked for
        while self.npass < self.total_points_requested:

            # Guarantee that there is no division by 0
            if abs(self.efficiency - 0.0) < 1e-12:
                self.efficiency = 1.0

            # Calculate number of points needed for next iteration -- round up to nearest whole number
            num_points_requested = math.ceil((self.total_points_requested-self.npass)/self.efficiency)

            # Print number of points that pass so far
            self.logger.debug(f"{self.npass} of {self.total_points_requested} requested points done")

            # Print number of points requested
            self.logger.debug(f'Generating {num_points_requested} points')

            # Run ScannerS
            points = run_scannerS(ini_name = ini_name,
                                  num_points = num_points_requested,
                                  model_name = param_space.model_name)

            # Update the total points run
            self.curr_points_run += points

            # Print info about applying filters
            self.logger.debug("Applying filters...")

            # Apply filters
            results = apply_filters(file_name = temp_tsv,
                                    model = param_space.model,
                                    config_loader = self.config_loader)

            # Concatenate the information from temp_tsv to the tsv file
            save_tsv_output(temp_tsv, tsv_name)

            # Update the numbers of events passing filters
            self.nwidth += results["width"]
            self.nbounds += results["bounds"]
            self.nsignals += results["signals"]
            self.npass += results["pass"]

            # Break if all points are being counted
            if not good_points_only:
                break

            # Calculate the running efficiency of the points passed based on points run so far
            if self.npass == 0 or self.curr_points_run == 0:
                running_efficiency = 1.0
            else:
                running_efficiency = self.npass / self.curr_points_run

            # Print points passed and efficiency
            self.logger.debug(f'{results["pass"]} points passed the filters with an efficiency of {100*running_efficiency:.1f}%')
            self.logger.debug(f'A total of {self.npass} points have passed')

            # Determine whether to adjust or keep the current efficiency
            if abs((self.efficiency/running_efficiency)-1) > 0.05:
                # Print points passed and efficiency
                self.logger.debug(f'{results["pass"]} points passed the filters with an efficiency of {100*running_efficiency:.1f}%\n')
                # Update the efficiency to the running efficiency with a small cushion
                self.efficiency = running_efficiency * 0.98
            else:
                self.logger.debug(f'{results["pass"]} points passed the filters with a previous efficiency of {100*self.efficiency*1.02:.1f}%\n')

        # Print final number of events that pass
        self.logger.info(f"Generated {self.npass} points that pass filters")
        self.logger.debug(f'{self.curr_points_run} generated, {self.npass} pass filters')

        # Create parser from output .tsv
        self.parser.read_file(file_name=tsv_name)

        return self.parser

    def sample_single_point(self,
                            point: Point,
                            decay: str,
                            identifier = "") -> Point:

        # Set names of input .ini and output .tsv files
        out_name = point.model_name
        # Check if identifier is defined
        if identifier:
            out_name += "_" + identifier
        ini_name = self.ini_dir + out_name + ".ini"
        tsv_name = self.tsv_dir + out_name + ".tsv"
        temp_tsv = self.out_dir + point.model_name + ".tsv"

        # Write new .ini file from template and parameters
        point.write_ini(ini_name)

        # Initialize parser
        self.parser = Parse(point.model)

        # Print number of points requested
        self.logger.debug('Generating 1 point')

        try:
            # Run ScannerS
            run_scannerS_single_point(ini_name = ini_name,
                                      model_name = point.model_name)
        except TimeoutError:
            raise

        # Print info about applying filters
        self.logger.debug("Applying filters...")

        # Apply filters
        results = apply_filters(file_name = temp_tsv,
                                model = point.model,
                                config_loader = self.config_loader)

        # Concatenate the information from temp_tsv to the tsv file
        save_tsv_output(temp_tsv, tsv_name)

        # Update the filtered variables
        self.nwidth = results["width"]
        self.nbounds = results["bounds"]
        self.nsignals = results["signals"]
        self.npass = results["pass"]

        # Print points passed and efficiency
        self.logger.debug(f'A total of {self.npass} points have passed')

        # Print final number of events that pass
        self.logger.info(f"Generated {self.npass} points that pass filters")
        self.logger.debug(f'1 point generated, {self.npass} pass filters')

        # Create parser from output .tsv
        self.parser.read_file(file_name=tsv_name)

        return self.parser.get_max_xb_point(decay)

if __name__ == "__main__":
    pass
