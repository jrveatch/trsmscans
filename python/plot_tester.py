#!/usr/bin/env python3

import os
from typing import Dict, List, Tuple
import matplotlib.pyplot as plt
import pandas as pd
import itertools
import logging

from collections import defaultdict
from plot import Plot
from numpy.typing import NDArray
import glob
import configparser
from utils import file_utils
from utils.model import Model
import argparse
import logging
from utils.params import Params
from utils.parse import Parse
class PlotTester:

    def __init__(self,
                 decay: str,
                 model: 'Model'):
        
        # Save arguments as class members
        self.decay = decay
        self.model = model
        self.scan_dir = file_utils.scan_dir(self.model, self.decay)
        self.ini_dir = self.scan_dir + "files/ini/"

        self.params = Params(model=self.model,
                             decay=decay)
        
        # Initialize parser
        self.parser = Parse(self.params.model)

        # get logger
        self.logger = logging.getLogger(self.__class__.__name__)

        # Create plot output directory
        self.output_dir = file_utils.plots_dir(model=self.model, 
                                               decay=self.decay)
        self.output_dir += "prescan_subsets/" # Add a new directory to hold the prescan plots apart from the scan plots
        os.makedirs(self.output_dir, exist_ok=True)

        # Parse ini files and store ranges
        self.ini_ranges = self.parse_ini_files(self.ini_dir)

        self.load_prescan_data()
        self.filter_data()
        self.plot_data()

    def parse_ini_files(self, directory):
        ranges_dict = {}  # Dictionary to store ranges for each file
        params_of_interest = ["t1", "t2", "t3", "vs", "vx"]

          # Collect all .ini files in the directory
        ini_files = glob.glob(os.path.join(directory, "*.ini"))
        # Sort the files (this can be sorted based on filename, date, etc.)
        self.sorted_ini_files = sorted(ini_files)

        # Loop through all .ini files in the directory
        for file_name in self.sorted_ini_files:
                file_path = os.path.join(directory, file_name)
                config = configparser.ConfigParser()
                config.read(file_path)

                ranges = {}
                for param in params_of_interest:
                    if param in config["scan"]:
                        min_val, max_val = map(float, config["scan"][param].split())
                        ranges[param] = (min_val, max_val)
                        #print(ranges[param])

                # Store the extracted ranges with the filename as key
                ranges_dict[file_name] = ranges

        '''# Print extracted ranges
        for file, ranges in ranges_dict.items():
            print(f"{file}: {ranges}")

            for i in ranges.items():
                print(i[1])

                min_v, max_v = i[1]
                print(f'min: {min_v} max: {max_v}')
        '''

        return ranges_dict
    
    def load_prescan_data(self):
        #Initialize the prescan directory that will be used to gather points
        self.prescan_tsv = file_utils.prescan_tsv(self.model)
        
        self.parser.read_file(file_name=self.prescan_tsv)

        self.panda_df = self.parser.filtered_data

        self.panda_df = self.panda_df[['thetahS','thetahX','thetaSX','vs','vx']]

       # print(self.panda_df)

    def filter_data(self):
        """Filter self.panda_df based on parameter ranges from .ini files."""
        if self.panda_df.empty or not self.ini_ranges:
            self.logger.warning("No data to filter.")
            return

        # Define mapping between .ini file params and DataFrame columns
        self.param_mapping = {
            "t1": "thetahS",
            "t2": "thetahX",
            "t3": "thetaSX",
            "vs": "vs",
            "vx": "vx"
        }

        #print(f'original:\n {self.panda_df}')

        self.filtered_files = {}

        for file, ranges in self.ini_ranges.items():
            filtered_df = self.panda_df.copy()
            filter_condition = pd.Series(True, index=filtered_df.index)
            for param, (min_val, max_val) in ranges.items():
                par_name = self.param_mapping.get(param)
                filter_condition &= (filtered_df[par_name]>min_val) & (filtered_df[par_name]<max_val)
            filtered_df = filtered_df[filter_condition]
            # Store the filtered DataFrame under the filename key
            self.filtered_files[file] = filtered_df

      #  print(self.filtered_files)

        self.load_data(self.filtered_files)
            
    def load_data(self, dictionary):

        self.pars = ['thetahS','thetahX','thetaSX','vs','vx']

        # Dictionary to store parameters together
        self.all_params = defaultdict(list)

        # Loop through ini_ranges and collect all parameter values together
        for file, df in dictionary.items():

            for param in self.pars:
                self.all_params[param].append(df[param].values.tolist())

        # Convert defaultdict back to a regular dict
        self.all_params = dict(self.all_params)

    '''def plot_data(self):
        """Generate scatter plots for all unique parameter pairs."""
        if self.filtered_df.empty:
            self.logger.warning("No data to plot.")
            return

        self.var_lists: Dict[str, List[NDArray]] = defaultdict(list)

        # Get all possible pairs of variables
        param_pairs = list(itertools.combinations(self.var_lists, 2))

        for x_param, y_param in param_pairs:
            plt.figure(figsize=(8, 6))
            plt.scatter(self.filtered_df[x_param], self.filtered_df[y_param], alpha=0.5)
            plt.xlabel(x_param)
            plt.ylabel(y_param)
            plt.title(f"{x_param} vs {y_param}")
            plt.grid(True)

            plot_path = os.path.join(self.output_dir, f"{x_param}_vs_{y_param}.png")
            plt.savefig(plot_path)
            plt.close()

            self.logger.info(f"Saved plot: {plot_path}")'''

    def plot_data(self) -> None:

        # Print info to screen
        print("Making scan plots for",self.model.name,self.decay,self.model.mass_string)

        num_files = len(self.sorted_ini_files)

        # Set the start and end colors by random RGB values
        start_rgb, end_rgb = self.select_colors()

        for i in range(len(self.pars)-1):

            var1_name = self.pars[i]
            var1 = self.all_params[var1_name]

            print(var1_name)
          #  print(var1)
            print(len(var1[i]))

            for j in range(i+1, len(self.pars)):

                var2_name = self.pars[j]
                var2 = self.all_params[var2_name]

                op = (0.8/num_files)
                opacity = op + 0.19

                plt.figure()

                for r, (v1, v2) in enumerate(zip(var1, var2)):

                    t = r/num_files
                    color = [start_rgb[c] + t * (end_rgb[c]-start_rgb[c]) for c in range(3)]

                    # Plot the variables by file
                    plt.scatter(v1, v2, s=15, color=color, alpha=opacity)

                    # Adjust the opacity
                    opacity += op 

                # Reset opacity for star points
                opacity = op
                opacity += 0.19
        # Initialize scatter plot labels
                plt.title(f"{var1_name} vs {var2_name}")
                plt.xlabel(f"{var1_name}")
                plt.ylabel(f"{var2_name}")

                # Save the figure as a .png
                plt.savefig(self.output_dir + f"scan_{var1_name}_vs_{var2_name}.png")

                # Close the figure
                plt.close()

        return

                

        '''# Iterate through the list of all variables to plot each variable combination from each file
        for v in range(self.num_vars-1):

            # Get the first variable 2D-list from the all variable list
            var1 = self.var_lists[self.var_names[v]]
            
            for j in range(v+1, self.num_vars):

                # Get the second variable 2D-List from the all variable list
                var2 = self.var_lists[self.var_names[j]]

                # Set the opacity to be between values 0.19 and 1 depending on the number of files
                op = (0.8 / self.num_files)
                opacity = op + 0.19

                # Create a new scatter figure
                plt.figure()

                # Iterate through both variable 2D-Lists to plot the info from each file
                for i in range(len(self.var_lists['xb'])):

                    # Decipher the color used for the scatter plot
                    t = i / self.num_files
                    color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                    # Plot the variables by file
                    plt.scatter(var1[i], var2[i], s=15, color=color, alpha=opacity)

                    # Adjust the opacity
                    opacity += op 

                # Reset opacity for star points
                opacity = op
                opacity += 0.19

                for q in range(len(self.var_lists['xb'])):

                    # Initialize both variables to be retrieved from the Point
                    variable1 = self.var_names[v]
                    variable2 = self.var_names[j]

                    # Get and store the max points for each variable
                    point1 = self.max_point_list[q].get_val(variable1)
                    point2 = self.max_point_list[q].get_val(variable2)

                    # Plot the max point from the scatter plot [star]
                    if(self.max_point_list[q] != maximum): #Make sure the point is not the maximum point
                        plt.scatter(point1, point2, s=25, color="yellow", alpha=opacity, marker="*") #plot normally
                    else: #If point is maximum point plot as a bigger star
                        plt.scatter(point1, point2, s=60, color="gold", alpha=0.999, marker="*")

                    # Adjust the opacity
                    opacity += op

                # Initialize scatter plot labels
                plt.title(f"{self.var_names[v]} vs {self.var_names[j]}")
                plt.xlabel(f"{self.var_names[v]}")
                plt.ylabel(f"{self.var_names[j]}")

                # Save the figure as a .png
                plt.savefig(self.output_dir + f"scan_{self.var_names[v]}_vs_{self.var_names[j]}.png")

                # Close the figure
                plt.close()

        return
  
# Plot the maximum xb in 2D bins for every parameter pair
    def make_scan_plots(self) -> None:

        # Print info to screen
        print("Making scan plots for",self.model.name,self.decay,self.model.mass_string)

        # Find the Maximum point from the maximum points
        maximum = max(self.max_point_list)

        # Set the start and end colors by random RGB values
        start_rgb, end_rgb = self.select_colors()

        # Iterate through the list of all variables to plot each variable combination from each file
        for v in range(self.num_vars-1):

            # Get the first variable 2D-list from the all variable list
            var1 = self.var_lists[self.var_names[v]]
            
            for j in range(v+1, self.num_vars):

                # Get the second variable 2D-List from the all variable list
                var2 = self.var_lists[self.var_names[j]]

                # Set the opacity to be between values 0.19 and 1 depending on the number of files
                op = (0.8 / self.num_files)
                opacity = op + 0.19

                # Create a new scatter figure
                plt.figure()

                for i in range():
                    pass

                # Iterate through both variable 2D-Lists to plot the info from each file
                for i in range(len(self.var_lists['xb'])):

                    # Decipher the color used for the scatter plot
                    t = i / self.num_files
                    color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                    # Plot the variables by file
                    plt.scatter(var1[i], var2[i], s=15, color=color, alpha=opacity)

                    # Adjust the opacity
                    opacity += op 

                # Reset opacity for star points
                opacity = op
                opacity += 0.19

                for q in range(len(self.var_lists['xb'])):

                    # Initialize both variables to be retrieved from the Point
                    variable1 = self.var_names[v]
                    variable2 = self.var_names[j]

                    # Get and store the max points for each variable
                    point1 = self.max_point_list[q].get_val(variable1)
                    point2 = self.max_point_list[q].get_val(variable2)

                    # Plot the max point from the scatter plot [star]
                    if(self.max_point_list[q] != maximum): #Make sure the point is not the maximum point
                        plt.scatter(point1, point2, s=25, color="yellow", alpha=opacity, marker="*") #plot normally
                    else: #If point is maximum point plot as a bigger star
                        plt.scatter(point1, point2, s=60, color="gold", alpha=0.999, marker="*")

                    # Adjust the opacity
                    opacity += op

                # Initialize scatter plot labels
                plt.title(f"{self.var_names[v]} vs {self.var_names[j]}")
                plt.xlabel(f"{self.var_names[v]}")
                plt.ylabel(f"{self.var_names[j]}")

                # Save the figure as a .png
                plt.savefig(self.output_dir + f"scan_{self.var_names[v]}_vs_{self.var_names[j]}.png")

                # Close the figure
                plt.close()

        return
   '''

    # Function that defines colors to plot using random RGB values
    def select_colors(self):

        # Define blue and red as the starting and stopping colors
        color1 = (0, 0, 1)
        color2 = (1, 0, 0)

        # Return the values to call
        return color1, color2

    '''
    def load_prescan(self):

        # Retrieve the variable names for the model
        self.var_names = self.model.input_parameter_names

        # Get number of variables for easy access
        self.num_vars = len(self.var_names)

        # Initialize list that will hold all the maximum points for each file iteration
        self.max_point_list: List[Point] = []

        # Initialize a dictionary to store lists of numpy arrays
        self.var_lists: Dict[str, List[NDArray]] = defaultdict(list)
        
        # Retrieve the variables from the file
        parser = Parse(file_name=self.prescan_tsv,
                        model=self.model)
        all_params = parser.input_parameter_arrays
        xb = parser.get_xb(self.decay)
        max_point = parser.get_max_xb_point(self.decay)

        # Iterate through the information of each parameter
        for name, par in all_params.items():

            # Append the variable value to the corresponding list
            self.var_lists[name].append(par)

        # Append the maximum point to the list
        self.max_point_list.append(max_point)

        # Empty array that will hold the files found
        self.all_files_dict: Dict[str, List[str]] = defaultdict(list)

    def get_ini_files(self) -> None: 
        # Directory for the scan outputs
        directory = file_utils.scan_dir(model=self.model,
                                        decay=self.decay) + "files/ini/"

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if file_name.endswith(".ini"):
                key = file_name.rsplit("-", 1)[-1].rsplit(".", 1)[0]
                self.all_files_dict[key].append(directory + file_name)

        # Store number of files for easy access
        self.num_files = sum(len(lst) for lst in self.all_files_dict.values())

        ________________________NOTES___________________________
        - Enter a prescan and retrive points from the prescan, get the zoom_optimizer list and traverse through those
        - take a presecan and plot only the points from zoom_optimizer ranges

        - When a zoom optimizer is made go to this plot tester class
        
        
        '''
if __name__ == "__main__":

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--decay", required=True, type=str)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float)
    arg_parser.add_argument("-S", "--SMass", required=True, type=float)
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float)
    arg_parser.add_argument("-M", "--model", default="TRSMBroken", type=str)
    args = arg_parser.parse_args()

    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})
    
    PlotTester(decay=args.decay, model=model)

    plotter = Plot(decay=args.decay, model=model)