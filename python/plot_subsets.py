#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import logging

import re
from collections import defaultdict
from plot import Plot
import glob
import configparser
from utils import file_utils
from utils.model import Model
import argparse
import logging
from utils.parse import Parse

logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s - %(message)s"
)

class PlotTester:

    def __init__(self,
                 decay: str,
                 model: 'Model'):
        
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
                        directory: str) -> dict:
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
    
    # Method to Load the information of the prescan to a Pandas Data Frame
    def load_prescan_data(self) -> None:
        """
        Load the prescan data into a pandas DataFrame using the Parse class.
        
        The DataFrame is filtered to keep only relevant columns defined in `param_mapping`.
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
        self.df = self.df[['thetahS','thetahX','thetaSX','vs','vx']]

        self.logger.debug(f'Panda Data Frame:\n\t{self.df}')

    def filter_data(self) -> None:
        """
        Filter the prescan DataFrame using the parameter ranges from the parsed .ini files.

        The filtered data is stored in a dictionary mapping each .ini filename to a filtered DataFrame.
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
        Generate 2D scatter plots for all parameter pairs.

        Each plot overlays scan points and bounding boxes corresponding to parameter regions
        from each .ini file grouped by Zoom Optimizer. Results are saved as PNG files.
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

                    # Save the figure as a .png
                    plt.savefig(os.path.join(group_output_dir,f"scan_{param1}__vs__{param2}.png"))

                    # Close the figure
                    plt.close()

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
    
    PlotTester(decay=args.decay, model=model)

    plotter = Plot(decay=args.decay, model=model)