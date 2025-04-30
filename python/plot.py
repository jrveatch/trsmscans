#!/usr/bin/env python3

# standard libraries
import argparse
from collections import defaultdict
from functools import cached_property
from itertools import combinations
import os
from typing import Dict, List, Tuple

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
                 model: Model):

        # Save arguments as class members
        self.decay = decay
        self.model = model

        # Create plot output directory
        self.output_dir = os.path.join(file_utils.plots_dir(model=self.model,decay=self.decay),"zoom")
        os.makedirs(self.output_dir, exist_ok=True)

        # Get list of .tsv files
        self.get_file_names()

        # Load data from all of the .tsv files
        self.load_data()

    @cached_property
    def var_names(self) -> Tuple[str, ...]:
        """
        Get the variable names for the model.
        """
        names = self.model.input_parameter_names
        if 'xb' in names:
            return names
        return names + ('xb',)

    @cached_property
    def num_vars(self) -> int:
        """
        Get the number of variables for the model.
        """
        return len(self.var_names)

    def get_file_names(self) -> None:
        """
        Get the list of .tsv files for plotting.
        """

        # Empty array that will hold the files found
        self.all_files_dict: Dict[str, List[str]] = defaultdict(list)

        # If prescan exists, make it the first file to plot
        prescan = file_utils.prescan_tsv(model=self.model)
        if os.path.exists(prescan):
            self.all_files_dict["Pre"].append(prescan)

        # Directory for the scan outputs
        directory = os.path.join(file_utils.scan_dir(model=self.model,decay=self.decay),"files","tsv")

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if file_name.endswith(".tsv"):
                key = file_name.rsplit("-", 1)[-1].rsplit(".", 1)[0]
                self.all_files_dict[key].append(os.path.join(directory,file_name))

    def load_data(self) -> None:
        """
        Load parameter arrays and max-xb Points from all .tsv files.
        Store combined parameter arrays for each iteration in self.var_lists.
        Store max-xb Point per iteration in self.max_point_list.
        """

        self.max_point_list: List[Point] = []
        self.var_lists: Dict[str, List[NDArray]] = defaultdict(list)

        # Loop through each group of files (e.g. Pre, 0, 1, ...)
        for file_list in self.all_files_dict.values():

            grouped_vars: Dict[str, List[NDArray]] = defaultdict(list)
            best_point: Point = None

            for file_name in file_list:
                parser = Parse(file_name=file_name, model=self.model)
                all_params = parser.input_parameter_arrays
                xb = parser.get_xb(self.decay)
                this_max = parser.get_max_xb_point(self.decay)

                for name, array in all_params.items():
                    grouped_vars[name].append(array)
                grouped_vars['xb'].append(xb)

                if best_point is None or this_max > best_point:
                    best_point = this_max

            # Concatenate all arrays in this group and append to self.var_lists
            for key, arrays in grouped_vars.items():
                self.var_lists[key].append(np.concatenate(arrays))

            self.concatenated_vars = {key: np.concatenate(val_list) for key, val_list in self.var_lists.items()}

            self.max_point_list.append(best_point)

    def plot_variable_pair(self, var1_name: str, var2_name: str) -> None:
        """
        Create a 2D scatter plot for a given pair of variables over all iterations.
        """
        var1 = self.var_lists[var1_name]
        var2 = self.var_lists[var2_name]

        op = 0.8 / len(self.var_lists['xb'])
        opacity = op + 0.19

        fig, ax = plt.subplots()
        for i in range(len(self.var_lists['xb'])):
            t = i / len(self.var_lists['xb'])
            color = plt.cm.viridis(t)
            ax.scatter(var1[i], var2[i], s=15, color=color, alpha=opacity)
            opacity += op

        maximum = max(self.max_point_list)
        for i, point in enumerate(self.max_point_list):
            point1 = point.get_val(var1_name)
            point2 = point.get_val(var2_name)
            if point != maximum:
                ax.scatter(point1, point2, s=25, color="orange", alpha=0.8, marker="*")
            else:
                max_point_1 = point1
                max_point_2 = point2

        ax.scatter(max_point_1, max_point_2, s=60, color="red", alpha=0.999, marker="*")
        ax.set_title(f"{var1_name} vs {var2_name}")
        ax.set_xlabel(var1_name)
        ax.set_ylabel(var2_name)
        fig.savefig(os.path.join(self.output_dir, f"scan_{var1_name}_vs_{var2_name}.png"))
        plt.close()

    def make_scan_plots(self) -> None:
        """
        Iterate over all unique pairs of variables and plot them.
        """
        print("Making scan plots for", self.model.name, self.decay, self.model.mass_string)
        for var1, var2 in combinations(self.var_names, 2):
            self.plot_variable_pair(var1, var2)

    def plot_max_xb_heatmap(self, var1_name: str, var2_name: str, num_bins: int = 100) -> None:
        """
        Plot a 2D heatmap showing the maximum xb in each bin of var1 vs var2.
        """
        df_comb = pd.DataFrame({key: self.concatenated_vars[key] for key in (var1_name, var2_name, 'xb')})

        # Bin the variables
        df_comb[f'{var1_name}_bin'] = pd.cut(df_comb[var1_name], bins=num_bins, labels=False)
        df_comb[f'{var2_name}_bin'] = pd.cut(df_comb[var2_name], bins=num_bins, labels=False)

        # Group by binned values and compute max xb
        max_xb_in_bins = df_comb.groupby([f'{var1_name}_bin', f'{var2_name}_bin'])['xb'].max().unstack(fill_value=np.nan)

        # Plot the heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(max_xb_in_bins.T,
                       origin='lower',
                       aspect='auto',
                       extent=[
                           df_comb[var1_name].min(), df_comb[var1_name].max(),
                           df_comb[var2_name].min(), df_comb[var2_name].max()
                           ],
                       cmap='viridis',
                       interpolation='bilinear')
        fig.colorbar(im, ax=ax, label='Maximum value of xb')
        ax.set_xlabel(var1_name)
        ax.set_ylabel(var2_name)
        ax.set_title(f'{var1_name} vs {var2_name}')
        fig.savefig(os.path.join(self.output_dir, f"maxxb_{var1_name}_vs_{var2_name}.png"))
        plt.close()

    def make_max_xb_plots(self) -> None:
        """
        Create a heatmap of the maximum xb for all unique variable pairs (excluding xb).
        """
        print("Making max XB plots for", self.model.name, self.decay, self.model.mass_string)
        for var1, var2 in combinations(self.var_names, 2):
            if 'xb' not in (var1, var2):
                self.plot_max_xb_heatmap(var1, var2)

if __name__ == '__main__':

    arg_parser = argparse.ArgumentParser()
    arg_parser.add_argument("-X", "--XMass", required=True, type=float)
    arg_parser.add_argument("-S", "--SMass", required=True, type=float)
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float)
    arg_parser.add_argument("-d", "--decay", required=True, type=str)
    arg_parser.add_argument("-m", "--model", required=True, type=str)
    args = arg_parser.parse_args()

    # Create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    plotter = Plot(decay=args.decay, model=model)
    plotter.make_scan_plots()
    plotter.make_max_xb_plots()
