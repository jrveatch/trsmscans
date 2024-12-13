#!/usr/bin/env python3

# standard libraries
import logging
from typing import List

# local modules
import filters.filter
from utils.config_loader import ConfigLoader
from utils.params import Params
from utils.parse import Parse
from utils.runScannerS import runScannerS
from utils.tsv_utils import save_tsv_output


class PointSampler:
        
    # Initializer: passes output directory, model name, and config loader
    def __init__(self,
                 out_dir: str,
                 model_name: str,
                 use_multiprocessing: bool,
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
        self.model_name = model_name
        self.use_multiprocessing = use_multiprocessing
        self.config_loader = config_loader

    # Method to sample a number of points
    def sample_points(self,
                      params: Params,
                      identifier: str,
                      npoints: int,
                      good_points_only: bool = True) -> Parse:

        # set names of input .ini and output .tsv files
        out_name = self.model_name + "_" + identifier
        ini_name = self.ini_dir + out_name + ".ini"
        tsv_name = self.tsv_dir + out_name + ".tsv"
        temp_tsv = self.out_dir + self.model_name + ".tsv"

        # Global variable for number of points
        self.npoints = npoints

        # write new .ini file from template and parameters
        params.write_ini(ini_name)

        # Initialize parser
        self.parser = Parse(params.masses(), self.model_name)

        # Initialize global variables given by filters
        self.nwidth = 0
        self.nbounds = 0
        self.npass = 0
        self.nsignals = 0

        # Initialize the amount of points run
        self.curr_points_run = 0

        # Print total number of points requested
        self.logger.info(f"{self.npoints} points requested")

        # Run until points passed is >= points asked for
        while self.npass < self.npoints:

            # Print number of points that pass so far
            self.logger.debug(f"{self.npass} of {self.npoints} requested points done")

            # Print number of points requested
            self.logger.debug(f'Generating {npoints} points')

            # Run ScannerS
            points = runScannerS(ini_name = ini_name,
                                 num_points = npoints,
                                 model_name = self.model_name,
                                 use_multiprocessing = self.use_multiprocessing)

            # Update the total points run
            self.curr_points_run += points

            # Print info about applying filters
            self.logger.debug("Applying filters...")

            # Apply width and bounds filters
            nwidth, nbounds, nsignals, npass = filters.filter.apply_filters(file_name = temp_tsv,
                                                                            masses = params.masses(),
                                                                            config_loader = self.config_loader)

            # Concatenate the information from temp_tsv to the tsv file
            save_tsv_output(temp_tsv, tsv_name)

            # Update the filtered variables
            self.npass += npass
            self.nbounds += nbounds
            self.nwidth += nwidth
            self.nsignals += nsignals

            # Break if all points are being counted
            if not good_points_only:
                break

            # Calculate the efficiency of the points passed based on points run
            efficiency = self.npass/self.curr_points_run

            # Print points passed and efficiency
            self.logger.debug(f'{npass} points passed the filters with an efficiency of {100*efficiency:.1f}%')
            self.logger.debug(f'A total of {self.npass} points have passed')

            # Add cushion to the efficiency
            efficiency *= 1.05

            # Calculate number of points needed for next iteration -- round to nearest whole number
            npoints = round((self.npoints-self.npass)/efficiency)

        # Print final number of events that pass
        self.logger.info(f"Generated {self.npass} points that pass filters")
        self.logger.debug(f'{self.curr_points_run} generated, {self.npass} pass filters')

        # Create parser from output .tsv
        self.parser.read_file(file_name=tsv_name)

        return self.parser

    # Return the variables
    def get_nwidth(self) -> int:
        return self.nwidth

    def get_nbounds(self) -> int:
        return self.nbounds

    def get_nsignals(self) -> int:
        return self.nsignals

    def get_npass(self) -> int:
        return self.npass

    def total_points_run(self) -> int:
        return self.curr_points_run

if __name__ == "__main__":
    pass
