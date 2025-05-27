#!/usr/bin/env python3

# standard libraries
import logging
import math
import os

# local modules
from utils.config_loader import ConfigLoader
from filters.filter import apply_filters
from utils.exceptions import NoPointsPassedError
from utils.param_space import ParamSpace
from utils.parse import Parse
from utils.point import Point
from utils.run_scannerS import run_scannerS, run_scannerS_single_point
from utils.tsv_utils import save_tsv_output

class PointSampler:
    """
    Handles sampling of parameter points for a given model and decay channel using ScannerS.

    Responsible for writing .ini files, invoking ScannerS, applying physics filters,
    saving results, and tracking sampling efficiency.
    """

    def __init__(self,
                 out_dir: str,
                 config_loader: ConfigLoader,
                 subdir_name: str = "") -> None:
        """
        Initializes a PointSampler with output directory and configuration.

        Args:
            out_dir (str): Base directory for outputs (ini, tsv).
            config_loader (ConfigLoader): Loader object for filter and scan config.
            subdir_name (str): Optional subdirectory for organizing ini/tsv outputs.
        """

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Initialize class variables
        self.out_dir = out_dir
        self.ini_dir = out_dir
        self.tsv_dir = out_dir
        if subdir_name:
            self.ini_dir = os.path.join(self.ini_dir,subdir_name,"ini")
            self.tsv_dir = os.path.join(self.tsv_dir,subdir_name,"tsv")
        self.config_loader = config_loader
        self.efficiency = 1.0

    @property
    def n_width(self) -> int:
        """Returns the number of points passing the width filter."""
        return self.__n_width

    @n_width.setter
    def n_width(self,
                new_n_width: int) -> None:
        """Sets the number of points passing the width filter."""
        self.__n_width = new_n_width

    @property
    def n_bounds(self) -> int:
        """Returns the number of points passing the bounds filter."""
        return self.__n_bounds

    @n_bounds.setter
    def n_bounds(self,
                 new_n_bounds: int) -> None:
        """Sets the number of points passing the bounds filter."""
        self.__n_bounds = new_n_bounds

    @property
    def n_signals(self) -> int:
        """Returns the number of points passing the signals filter."""
        return self.__n_signals

    @n_signals.setter
    def n_signals(self,
                  new_n_signals: int) -> None:
        """Sets the number of points passing the signals filter."""
        self.__n_signals = new_n_signals

    @property
    def n_pass(self) -> int:
        """Returns the number of points passing all filters."""
        return self.__n_pass

    @n_pass.setter
    def n_pass(self,
               new_n_pass: int) -> None:
        """Sets the number of points passing all filters."""
        self.__n_pass = new_n_pass

    @property
    def total_points_run(self) -> int:
        """Returns the total number of points generated so far."""
        return self.curr_points_run

    def sample_points(self,
                      param_space: ParamSpace,
                      num_points_requested: int,
                      identifier = "",
                      good_points_only: bool = False) -> Parse:
        """
        Samples multiple parameter points using ScannerS until the desired number of points
        pass all filters. Writes to .ini/.tsv files and returns a Parse object with results.

        Args:
            param_space (ParamSpace): The parameter space to sample from.
            num_points_requested (int): Number of accepted points desired.
            identifier (str): Optional tag to distinguish output files.
            good_points_only (bool): If True, continues sampling until enough good points are found.

        Returns:
            Parse: A Parse object containing the filtered and analyzed results.

        Raises:
            NoPointsPassedError: If no points pass the filters in the first batch.
        """

        # Set names of input .ini and output .tsv files
        out_name = param_space.model_name
        # Check if identifier is defined
        if identifier:
            out_name += "_" + identifier
        ini_name = os.path.join(self.ini_dir,f"{out_name}.ini")
        tsv_name = os.path.join(self.tsv_dir,f"{out_name}.tsv")
        temp_tsv = os.path.join(self.out_dir,f"{param_space.model_name}.tsv")

        # Global variable for number of points
        self.total_points_requested = num_points_requested

        # Write new .ini file from template and parameters
        param_space.write_ini(ini_name)

        # Initialize parser
        self.parser = Parse(param_space.model)

        # Initialize filter counters
        self.n_width = 0
        self.n_bounds = 0
        self.n_signals = 0
        self.n_pass = 0

        # Initialize the amount of points run
        self.curr_points_run = 0

        # Print total number of points requested
        self.logger.info(f"{self.total_points_requested} points requested")

        # Run until points passed is >= points asked for
        while self.n_pass < self.total_points_requested:

            # Guarantee that there is no division by 0
            if abs(self.efficiency - 0.0) < 1e-12:
                self.efficiency = 1.0

            # Calculate number of points needed for next iteration -- round up to nearest whole number
            num_points_requested = math.ceil((self.total_points_requested-self.n_pass)/self.efficiency)

            # Print number of points that pass so far
            self.logger.debug(f"{self.n_pass} of {self.total_points_requested} requested points done")

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
            self.n_width += results["width"]
            self.n_bounds += results["bounds"]
            self.n_signals += results["signals"]
            self.n_pass += results["pass"]

            # If no points passed the filters, raise an error
            if self.n_pass == 0:
                self.logger.error("No points passed the filters")
                self.logger.debug(f'{self.curr_points_run} generated, {self.n_pass} pass filters')
                raise NoPointsPassedError()

            # Break if all points are being counted
            if not good_points_only:
                break

            # Calculate the running efficiency of the points passed based on points run so far
            running_efficiency = self.n_pass / self.curr_points_run

            # Print points passed and efficiency
            self.logger.debug(f'{results["pass"]} points passed the filters with an efficiency of {100*running_efficiency:.1f}%')
            self.logger.debug(f'A total of {self.n_pass} points have passed')

            # Determine whether to adjust or keep the current efficiency
            if abs((self.efficiency/running_efficiency)-1) > 0.05:
                # Print points passed and efficiency
                self.logger.debug(f'{results["pass"]} points passed the filters with an efficiency of {100*running_efficiency:.1f}%\n')
                # Update the efficiency to the running efficiency with a small cushion
                self.efficiency = running_efficiency * 0.98
            else:
                self.logger.debug(f'{results["pass"]} points passed the filters with a previous efficiency of {100*self.efficiency*1.02:.1f}%\n')

        # Print final number of events that pass
        self.logger.info(f"Generated {self.n_pass} points that pass filters")
        self.logger.debug(f'{self.curr_points_run} generated, {self.n_pass} pass filters')

        # Create parser from output .tsv
        self.parser.read_file(file_name=tsv_name)

        return self.parser

    def sample_single_point(self,
                            point: Point,
                            decay: str,
                            identifier = "") -> Point:
        """
        Evaluates a single parameter point using ScannerS and returns the best xb result.

        Args:
            point (Point): The parameter point to evaluate.
            decay (str): The decay mode to use for calculating xb.
            identifier (str): Optional tag for output file names.

        Returns:
            Point: The best point based on xb (should match input if only one was evaluated).

        Raises:
            TimeoutError: If ScannerS fails to complete within time limits.
        """

        # Set names of input .ini and output .tsv files
        out_name = point.model_name
        # Check if identifier is defined
        if identifier:
            out_name += "_" + identifier
        ini_name = os.path.join(self.ini_dir,f"{out_name}.ini")
        tsv_name = os.path.join(self.tsv_dir,f"{out_name}.tsv")
        temp_tsv = os.path.join(self.out_dir,f"{point.model_name}.tsv")

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
        self.n_width = results["width"]
        self.n_bounds = results["bounds"]
        self.n_signals = results["signals"]
        self.n_pass = results["pass"]

        # Print points passed and efficiency
        self.logger.debug(f'A total of {self.n_pass} points have passed')

        # Print final number of events that pass
        self.logger.info(f"Generated {self.n_pass} points that pass filters")
        self.logger.debug(f'1 point generated, {self.n_pass} pass filters')

        # Create parser from output .tsv
        self.parser.read_file(file_name=tsv_name)

        return self.parser.get_max_xb_point(decay)

if __name__ == "__main__":
    pass
    # Script does not support direct execution
