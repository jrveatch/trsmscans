#!/usr/bin/env python3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import parse
import argparse
from utils import fileutils
from utils.masses import Masses
from utils.model import Model

# Plot class
class Plot:

    def __init__(self,
                 decay: str,
                 masses: 'Masses',
                 model_name: str):

        # Save arguments as class members
        self.decay = decay
        self.masses = masses
        self.model = Model(model_name)

        # Create plot output directory
        self.output_dir = fileutils.plots_dir(model_name=self.model.name(),
                                              decay=self.decay,
                                              masses=self.masses)
        os.makedirs(self.output_dir, exist_ok=True)

        # Get list of .tsv files
        self.get_file_names()

        # Load data from all of the .tsv files
        self.load_data()

    # Function to get list of .tsv files for plotting
    def get_file_names(self) -> None:

        # Empty array that will hold the files found
        self.all_files: list[str] = []

        # Directory for the scan outputs
        directory = fileutils.scan_dir(model_name=self.model.name(),
                                       decay=self.decay,
                                       masses=self.masses) + "files/tsv/"

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if ".tsv" in file_name:
                self.all_files.append(directory + file_name)

        # Sort the array so files are in order
        self.all_files.sort()

        # If prescan exists, make it the first file to plot
        prescan = fileutils.prescan_tsv(model_name=self.model.name(),
                                        masses=self.masses)
        if os.path.exists(prescan):
            self.all_files.insert(0, prescan)

        # Store number of files for easy access
        self.nfiles = len(self.all_files)

    # Function to load data from files
    def load_data(self) -> None:

        # Retrieve the variable names for the model
        self.var_names = self.model.parameter_names()

        # Check if xb exists in the variable name list, if not append
        if 'xb' not in self.var_names:
            self.var_names.append('xb')

        # Get number of variables for easy access
        self.nvars = len(self.var_names)

        # Initialize list that will hold all the maximum points for each file iteration
        self.maxpoint_list = []

        # Initialize a dictionary to store lists of numpy arrays
        self.var_lists = {}

        # Iterate through each file
        for file_name in self.all_files:

            # Retrieve the variables from the list
            parser = parse.Parse(file_name=file_name,
                                 masses=self.masses,
                                 model_name=self.model.name())
            allParams = parser.get_parameter_arrays()
            xb = parser.get_xb(self.decay)

            # Retrieve maximum point based on the file's variables
            maxpoint = parser.get_max_xb_point(self.decay)

            # Iterate through the information of each parameter
            for name, par in allParams.items():
            # Ensure the variable list exists for the parameter name

                #Check the parameter name
                if name not in self.var_lists:
                    self.var_lists[name] = []

                # Append the variable value to the corresponding list
                self.var_lists[name].append(par)

            # Check if xb exists in the variable list
            if 'xb' not in self.var_lists:
                self.var_lists['xb'] = []

            # Append xb to the corresponding list
            self.var_lists['xb'].append(xb)

            # Append the maximum point to the list
            self.maxpoint_list.append(maxpoint)

        # Initialize a dictionary to hold combined arrays
        self.comb_arrays = {}

        # Loop over dictionary of lists and concatenate them
        for vname, vlist in self.var_lists.items():
            self.comb_arrays[vname] = np.concatenate(vlist)

        # Store concatenated list as a pandas DataFrame
        self.df_comb = pd.DataFrame(self.comb_arrays)

        return

    # Plot each iteration of the scan
    # TODO: find a way to make the process more efficient and faster !!
    def make_scan_plots(self) -> None:

        # Print info to screen
        print("Making scan plots for",self.model.name(),self.decay,self.masses)

        # Find the Maximum point from the maximum points
        maximum = max(self.maxpoint_list)

        # Set the start and end colors by random RGB values
        start_rgb, end_rgb = self.select_colors()

        # Iterate through the list of all variables to plot each variable combination from each file
        for v in range(self.nvars-1):

            # Get the first variable 2D-list from the all variable list
            var1 = self.var_lists[self.var_names[v]]
            
            for j in range(v+1, self.nvars):

                # Get the second variable 2D-List from the all variable list
                var2 = self.var_lists[self.var_names[j]]

                # Set the opacity to be between values 0.19 and 1 depending on the number of files
                op = (0.8 / self.nfiles)
                opac = op + 0.19

                # Create a new scatter figure
                plt.figure()

                # Iterate through both variable 2D-Lists to plot the info from each file
                for i in range(len(self.var_lists['xb'])):

                    # Decipher the color used for the scatter plot
                    t = i / self.nfiles
                    color = [start_rgb[c] + t * (end_rgb[c] - start_rgb[c]) for c in range(3)]

                    # Plot the variables by file
                    plt.scatter(var1[i], var2[i], s=15, color=color, alpha=opac)

                    # Adjust the opacity
                    opac+=op 

                # Reset opacity for star points
                opac = op
                opac += 0.19

                for q in range(len(self.var_lists['xb'])):

                    # Initialize both variables to be retrieved from the Point
                    variable1 = self.var_names[v]
                    variable2 = self.var_names[j]

                    # Get and store the max points for each variable
                    point1 = self.maxpoint_list[q].get_val(variable1)
                    point2 = self.maxpoint_list[q].get_val(variable2)

                    # Plot the max point from the scatterplot [star]
                    if(self.maxpoint_list[q] != maximum): #Make sure the point is not the maximum point
                        plt.scatter(point1, point2, s=25, color="yellow", alpha=opac, marker="*") #plot normally
                    else: #If point is maximum point plot as a bigger star
                        plt.scatter(point1, point2, s=60, color="gold", alpha=0.999, marker="*")

                    # Adjust the opacity
                    opac+=op

                # Initialize scatterplot labels
                plt.title(f"{self.var_names[v]} vs {self.var_names[j]}")
                plt.xlabel(f"{self.var_names[v]}")
                plt.ylabel(f"{self.var_names[j]}")

                # Save the figure as a .png
                plt.savefig(self.output_dir + "scan_" + f"{self.var_names[v]}_vs_{self.var_names[j]}.png")

                # Close the figure
                plt.close()

        return

    # Plot the maximum xb in 2D bins for every parameter pair
    def make_max_xb_plots(self) -> None:

        # Print info to screen
        print("Making max XB plots for",self.model.name(),self.decay,self.masses)

        # Define number of bins to use in each dimension
        nbins = 100

        # Loop over var names and bin the corresponding columns
        for var in self.var_names:

            # Skip xb
            if var == 'xb':
                continue

            # Bin column
            self.df_comb[var+'_bin'] = pd.cut(self.df_comb[var], bins = nbins, labels = False)

        # Loop over var names twice to get every pair
        for v1 in range(self.nvars-1):

            # Get the first variable name from the all variable list
            var1 = self.var_names[v1]

            # Skip xb
            if var1 == 'xb':
                continue
            
            for v2 in range(v1+1, self.nvars):

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

        return
    
    # Function that defines colors to plot using random RGB values
    def select_colors(self):

        # Define blue and red as the starting and stopping colors
        color1 = (0, 0, 1)
        color2 = (1, 0, 0)

        # Return the values to call
        return color1, color2

if __name__ == '__main__':

    argparser = argparse.ArgumentParser()
    argparser.add_argument("-d", "--decay", required=True, type=str)
    argparser.add_argument("-X", "--XMass", required=True, type=float)
    argparser.add_argument("-S", "--SMass", required=True, type=float)
    argparser.add_argument("-H", "--HMass", default=125.09, type=float)
    argparser.add_argument("-M", "--model", default="TRSMBroken", type=str)
    args = argparser.parse_args()

    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    plotter = Plot(decay=args.decay, masses=masses, model_name=args.model)
    plotter.make_scan_plots()
    plotter.make_max_xb_plots()
