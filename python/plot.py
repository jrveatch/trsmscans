#!/usr/bin/env python3

# standard libraries
import argparse
import os
from collections import defaultdict
from typing import Dict, List

# third-party libraries
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from numpy.typing import NDArray

# local modules
from utils import file_utils
from utils.model import Model
from utils.parse import Parse
from utils.point import Point

# Plot class
class Plot:

    def __init__(self,
                 decay: str,
                 model: 'Model'):

        # Save arguments as class members
        self.decay = decay
        self.model = model

        # Create plot output directory
        self.output_dir = file_utils.plots_dir(model=self.model,
                                               decay=self.decay)
        os.makedirs(self.output_dir, exist_ok=True)

        # Get list of .tsv files
        self.get_file_names()

        # Load data from all of the .tsv files
        self.load_data()

    # Function to get list of .tsv files for plotting
    def get_file_names(self) -> None:

        # Empty array that will hold the files found
        self.all_files_dict: Dict[str, List[str]] = defaultdict(list)

        # If prescan exists, make it the first file to plot
        prescan = file_utils.prescan_tsv(model=self.model)
        if os.path.exists(prescan):
            self.all_files_dict["Pre"].append(prescan)

        # Directory for the scan outputs
        directory = os.path.join(file_utils.scan_dir(model=self.model,decay=self.decay), "files/tsv/")

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if file_name.endswith(".tsv"):
                key = file_name.rsplit("-", 1)[-1].rsplit(".", 1)[0]
                self.all_files_dict[key].append(directory + file_name)

        # Store number of files for easy access
        self.num_files = sum(len(lst) for lst in self.all_files_dict.values())

    # Function to load data from files
    def load_data(self) -> None:

        # Retrieve the variable names for the model
        self.var_names = list(self.model.input_parameter_names)

        # Check if xb exists in the variable name list, if not append
        if 'xb' not in self.var_names:
            self.var_names.append('xb')

        # Get number of variables for easy access
        self.num_vars = len(self.var_names)

        # Initialize list that will hold all the maximum points for each file iteration
        self.max_point_list: List[Point] = []

         # This will store raw per-file data before we concatenate
        per_file_data: List[Dict[str, NDArray]] = []

        # Loop through each iteration
        for file_list in self.all_files_dict.values():

            combined_params: Dict[str, List[NDArray]] = defaultdict(list)
            max_point: Point = None

            for file_name in file_list:

                # Retrieve the variables from the file
                parser = Parse(file_name=file_name,
                               model=self.model)
                all_params = parser.input_parameter_arrays
                xb = parser.get_xb(self.decay)
                this_max = parser.get_max_xb_point(self.decay)

                for name, par in all_params.items():
                    combined_params[name].append(par)
                combined_params['xb'].append(xb)

                if max_point is None or this_max > max_point:
                    max_point = this_max

            # Concatenate all arrays for this group
            concatenated: Dict[str, NDArray] = {
                key: np.concatenate(val_list) for key, val_list in combined_params.items()
            }

            per_file_data.append(concatenated)
            self.max_point_list.append(max_point)

        # Now split per_file_data into lists of arrays for each variable
        self.var_lists: Dict[str, List[NDArray]] = defaultdict(list)
        for entry in per_file_data:
            for key in entry:
                self.var_lists[key].append(entry[key])

        # Concatenate across all iterations
        self.comb_arrays = {
            key: np.concatenate(val_list) for key, val_list in self.var_lists.items()
        }

        # Create a DataFrame from the combined arrays
        self.df_comb = pd.DataFrame(self.comb_arrays)

    # Plot each iteration of the scan
    # TODO: find a way to make the process more efficient and faster !!
    def make_scan_plots(self) -> None:

        # Print info to screen
        print("Making scan plots for",self.model.name,self.decay,self.model.mass_string)

        # Find the Maximum point from the maximum points
        maximum = max(self.max_point_list)

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

                # Iterate through both variable 2D-Lists to plot the info from each file
                for i in range(len(self.var_lists['xb'])):

                    # Decipher the color used for the scatter plot
                    t = i / self.num_files
                    color = plt.cm.plasma(t)

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
                plt.savefig(os.path.join(self.output_dir, f"scan_{self.var_names[v]}_vs_{self.var_names[j]}.png"))

                # Close the figure
                plt.close()

    # Plot the maximum xb in 2D bins for every parameter pair
    def make_max_xb_plots(self) -> None:

        # Print info to screen
        print("Making max XB plots for",self.model.name,self.decay,self.model.mass_string)

        # Define number of bins to use in each dimension
        num_bins = 100

        # Loop over var names and bin the corresponding columns
        for var in self.var_names:

            # Skip xb
            if var == 'xb':
                continue

            # Bin column
            self.df_comb[var+'_bin'] = pd.cut(self.df_comb[var], bins = num_bins, labels = False)

        # Loop over var names twice to get every pair
        for v1 in range(self.num_vars-1):

            # Get the first variable name from the all variable list
            var1 = self.var_names[v1]

            # Skip xb
            if var1 == 'xb':
                continue

            for v2 in range(v1+1, self.num_vars):

                # Get the first variable name from the all variable list
                var2 = self.var_names[v2]

                # Skip xb
                if var2 == 'xb':
                    continue

                # Group by the bins and compute the maximum value of X in each bin
                max_xb_in_bins = self.df_comb.groupby([var1+'_bin', var2+'_bin'])['xb'].max().unstack(fill_value=np.nan)

                # Plotting
                plt.figure(figsize=(10, 8))
                plt.imshow(max_xb_in_bins.T,
                           origin='lower',
                           aspect='auto',
                           extent=[self.comb_arrays[var1].min(),
                                   self.comb_arrays[var1].max(),
                                   self.comb_arrays[var2].min(),
                                   self.comb_arrays[var2].max()],
                           cmap='viridis',
                           interpolation='bilinear')
                plt.colorbar(label='Maximum value of xb')
                plt.xlabel(var1)
                plt.ylabel(var2)
                plt.title(f'{var1} vs {var2}')

                # Save the figure as a .png
                plt.savefig(self.output_dir + 'maxxb_' + f'{var1}_vs_{var2}.png')

                # Close the figure
                plt.close()

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-d", "--decay", required=True, type=str)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float)
    arg_parser.add_argument("-S", "--SMass", required=True, type=float)
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float)
    arg_parser.add_argument("-M", "--model", default="TRSMBroken", type=str)
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    plotter = Plot(decay=args.decay, model=model)
    plotter.make_scan_plots()
    plotter.make_max_xb_plots()
