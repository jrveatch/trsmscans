#!/usr/bin/env python3

"""
Visualizes prescan subsets used during zoom scans.

This script reads `.ini` files from zoom scans to determine the parameter space
subsets, filters prescan data accordingly, and generates 2D scatter plots showing
how each region contributes to the scan.
"""

import argparse
from collections import defaultdict
import configparser
import glob
import logging
import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import re
from typing import Dict, Tuple

from utils import file_utils
from utils.model import Model
from utils.parse import Parse

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

class SubsetPlotter:
    """
    Plots prescan points filtered by parameter ranges defined in zoom `.ini` files.

    For each optimizer and iteration, subsets of prescan data are extracted and
    plotted alongside bounding boxes representing the scan range. This helps
    visualize how parameter space was explored over time.
    """

    def __init__(self,
                 decay: str,
                 model: Model):
        """
        Initializes the SubsetPlotter with model and decay information.

        This triggers loading and filtering of prescan data and automatic plot generation.

        Args:
            decay (str): Decay mode being studied.
            model (Model): Scalar model associated with the prescan.
        """
        
        # Save arguments as class members
        self.decay = decay
        self.model = model
        self.scan_dir = file_utils.scan_dir(self.model, self.decay)
        self.ini_dir = os.path.join(self.scan_dir,"zoom","ini")
        
        # Initialize parser
        self.parser = Parse(self.model)

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create plot output directory
        self.output_dir = os.path.join(file_utils.plots_dir(model=self.model,decay=self.decay),"prescan_subsets")
        os.makedirs(self.output_dir, exist_ok=True)

        # Parse ini files and store ranges
        self.ini_ranges = self.parse_ini_files(self.ini_dir)

        self.load_prescan_data()
        self.filter_data()
        self.plot_data()

    def parse_ini_files(self,
                        directory: str) -> Dict[str, Dict[str, Tuple[float, float]]]:
        """
        Parses `.ini` files to extract scan parameter ranges for each optimizer iteration.

        The result is a nested dictionary mapping each optimizer ID to a dictionary
        that maps `.ini` filenames to parameter bounds.

        Args:
            directory (str): Path to the directory containing `.ini` files.

        Returns:
            Dict[str, Dict[str, Tuple[float, float]]]: A dictionary of dictionaries containing
            parameter bounds (min, max) for each file, grouped by optimizer.
        """

        # Dictionary to store ranges for each file
        ranges_dict = defaultdict(dict) 

        # Collect all .ini files in the directory
        ini_files = glob.glob(os.path.join(directory, "*.ini"))

        # Sort the files by Zoom Optimizer and Iterations
        self.sorted_ini_files = sorted(ini_files)

        # Store params we need in list
        params_of_interest = ["t1", "t2", "t3", "vs", "vx"]

        # Print info
        self.logger.info(f"Parsing ini files from {directory}")

        # Loop through all .ini files in the directory
        for file_name in self.sorted_ini_files:
                
            # Create file path based on .ini file name
            file_path = os.path.join(directory, file_name)

            # Find the Zoom Optimizer used in the file and group all files by Zoom Optimizer
            if match := re.search(r"(ZoomOptimizer-\d+)", file_name):
                zoom_op_key = match.group(1)
            else:
                raise ValueError(f"Pattern not found in file_name: {file_name}")

            # Create config parse to read the path
            config = configparser.ConfigParser()
            config.read(file_path)

            # Initialize empty dictionary to store the range information
            ranges = {}

            # Iterate through each parameter
            for param in params_of_interest:

                # Extract the param from the .ini file
                if param in config["scan"]:

                    # Store min and max values for the param
                    min_val, max_val = map(float, config["scan"][param].split())
                    ranges[param] = (min_val, max_val)

            # Store the extracted ranges with the filename and Zoom Optimier as keys
            ranges_dict[zoom_op_key][file_name] = ranges

        # Debugger that prints the ranges from the .ini files
        self.logger.debug(f'Ini Range Data:\n\t{ranges_dict}')

        # Return to call
        return ranges_dict

    def load_prescan_data(self) -> None:
        """
        Loads prescan results into a pandas DataFrame.

        Reads the `.tsv` file using the `Parse` class and extracts only
        the input parameters relevant to the model.
        """

        # Print current status
        self.logger.info("Loading prescan...")

        # Initialize the prescan directory that will be used to gather points
        self.prescan_tsv = file_utils.prescan_tsv(self.model)
        
        # Read the data from the prescan file
        self.parser.read_file(file_name=self.prescan_tsv)

        # Retrieve attribute
        self.df = self.parser.filtered_data

        # Store the Pandas Data Frame by parameter keys
        self.df = self.df[list(self.model.input_parameter_full_names)]

        self.logger.debug(f'Panda Data Frame:\n\t{self.df}')

    def filter_data(self) -> None:
        """
        Filters the prescan DataFrame based on `.ini` parameter ranges.

        Stores a separate filtered DataFrame for each `.ini` file to be
        used in plotting scan coverage and boundaries.
        """

        # Filter self.df based on parameter ranges from .ini files.
        if self.df.empty or not self.ini_ranges:
            self.logger.warning("No data to filter.")
            return

        # Initialize empty dictionary to store filtered files
        self.filtered_files = {}

        # Loop through the ini_ranges by file name and zoom optimizer
        for data in self.ini_ranges.values():

            # Iterate through the file names and the ranfe data
            for file, ranges in data.items():

                # Make a copy of the Panda Data Frame
                filtered_df = self.df.copy()

                filter_condition = pd.Series(True, index=filtered_df.index)
                for param, (min_val, max_val) in ranges.items():
                    par_name = self.model.ini_name_to_fullname_map[param]
                    filter_condition &= (filtered_df[par_name]>min_val) & (filtered_df[par_name]<max_val)
                filtered_df = filtered_df[filter_condition]

                # Store the filtered DataFrame under the filename key
                self.filtered_files[file] = filtered_df

    def plot_data(self) -> None:
        """
        Generates and saves 2D scatter plots showing parameter subsets.

        For each pair of parameters and optimizer iteration, a plot is created
        that overlays prescan points with bounding boxes representing the scan region.
        Plots are grouped by optimizer and saved to PNG files.
        """

        # Print info to screen
        self.logger.info(f"Making scan plots for {self.model.name} {self.decay} {self.model.mass_string}")

        for zoom_op in self.ini_ranges.keys():
            
            # Retrieve files based on the current Zoom Optimizer
            zoom_op_files = {file: df for file, df in self.filtered_files.items() if re.search(zoom_op, file)}
                
            # Create a new output directory to organize output by Zoom Optimizer    
            group_output_dir = os.path.join(self.output_dir,zoom_op)
            os.makedirs(group_output_dir, exist_ok=True)

            for i, param1 in enumerate(self.model.input_parameter_full_names[:-1]):
                for param2 in self.model.input_parameter_full_names[i+1:]:
                    # Extract values for each file (filtered DataFrames)
                    param1_values = [zoom_op_files[file][param1].to_numpy(dtype=float) for file in zoom_op_files]
                    param2_values = [zoom_op_files[file][param2].to_numpy(dtype=float) for file in zoom_op_files]

                    num_files = len(param1_values)

                    op = (0.8/num_files)
                    opacity = op + 0.19
                    width=1.5

                    plt.figure()
               
                    for r, (file, v1, v2) in enumerate(zip(zoom_op_files, param1_values, param2_values)):

                        t = r/num_files
                        color = plt.cm.viridis(t)

                        # Plot the variables by file
                        plt.scatter(v1, v2, s=15, color=color, alpha=opacity)

                        file_ranges = self.ini_ranges[zoom_op][file]
                        self.logger.debug(file_ranges)

                        x_ini = self.model.fullname_to_ini_name_map[param1]
                        y_ini = self.model.fullname_to_ini_name_map[param2]

                        x_min, x_max = file_ranges[x_ini]
                        y_min, y_max = file_ranges[y_ini]

                        rect = patches.Rectangle(
                            (x_min, y_min),
                            x_max - x_min,
                            y_max - y_min,
                            linewidth=min(width + (r * 0.3), 5.0), # Gets thicker each iteration
                            edgecolor='black',
                            facecolor='none',
                            alpha= min(0.3 + r * op, 1.0) # Gets darker
                        )
                        plt.gca().add_patch(rect)

                        # Adjust the opacity
                        opacity += op 

                    # Initialize scatter plot labels
                    plt.title(f"{zoom_op}: {param1} vs {param2}")
                    plt.xlabel(f"{param1}")
                    plt.ylabel(f"{param2}")

                    # Better layout to prevent cropping
                    plt.tight_layout()

                    # Save the figure as a .png
                    plt.savefig(os.path.join(group_output_dir,f"scan_{param1}__vs__{param2}.png"))

                    # Close the figure
                    plt.close()

# Command-line entry point for generating prescan subset plots.
# Creates a SubsetPlotter instance and automatically loads, filters,
# and visualizes the subset scan regions from zoom `.ini` files.
if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--decay", required=True, type=str)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float)
    arg_parser.add_argument("-S", "--SMass", required=True, type=float)
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float)
    arg_parser.add_argument("-m", "--model", default="TRSMBroken", type=str)
    args = arg_parser.parse_args()

    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})
    
    SubsetPlotter(decay=args.decay, model=model)