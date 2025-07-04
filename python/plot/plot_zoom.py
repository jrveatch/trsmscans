
"""
Generates 2D scatter plots and heatmaps from scan results of scalar models.

This module visualizes parameter evolution and maximum xb values using data
from prescans and zoom scans, producing both overlaid scatter plots and
binned maximum-`xb` heatmaps.
"""

# standard libraries
from collections import defaultdict
from functools import cached_property
from itertools import combinations
import os
from typing import Dict, List, Tuple

# third-party libraries
import matplotlib.pyplot as plt
from matplotlib import cm
import numpy as np
import pandas as pd

# local modules
from utils import file_utils
from utils.model import Model
from utils.parse import Parse
from utils.point import Point

class ZoomPlotter:
    """
    Creates visualizations for scan results from scalar model parameter studies.

    This class loads `.tsv` files from prescans and zoom scans, processes
    parameter data, and generates a set of scatter plots and heatmaps to
    visualize the exploration and optimization of parameter space.
    """

    def __init__(self,
                 decay: str,
                 model: Model):
        """
        Initializes the Plot object with a model and decay mode.

        This automatically loads all available scan data for plotting.

        Args:
            decay (str): Decay channel used in the scans.
            model (Model): Scalar model associated with the scan results.
        """

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
        """Returns the input parameter names and includes 'xb' if not already present."""
        names = self.model.input_parameter_names
        if 'xb' in names:
            return names
        return (*names, 'xb')

    def get_file_names(self) -> None:
        """
        Finds and organizes all `.tsv` scan result files to be used for plotting.

        Categorizes files by prescan and each zoom scan iteration.
        """

        # Empty array that will hold the files found
        self.all_files_dict: Dict[str, List[str]] = defaultdict(list)

        # If prescan exists, make it the first file to plot
        prescan = file_utils.prescan_tsv(model=self.model)
        if os.path.exists(prescan):
            self.all_files_dict["Pre"].append(prescan)

        # Directory for the scan outputs
        directory = os.path.join(file_utils.scan_dir(model=self.model,decay=self.decay),"zoom","tsv")

        # Iterate through the directory
        for file_name in os.listdir(directory):

            # Check if the file is a .tsv file, if it is, append to the list
            if file_name.endswith(".tsv"):
                key = file_name.rsplit("-", 1)[-1].rsplit(".", 1)[0]
                self.all_files_dict[key].append(os.path.join(directory,file_name))

    def load_data(self) -> None:
        """
        Loads parameter arrays and maximum-xb points from all available `.tsv` files.

        Populates `self.var_lists` with parameter data and `self.max_point_list`
        with the best point from each group.
        """

        self.max_point_list: List[Point] = []
        self.var_lists: Dict[str, List[np.ndarray]] = defaultdict(list)

        # Loop through each group of files (e.g. Pre, 0, 1, ...)
        for file_list in self.all_files_dict.values():

            grouped_vars: Dict[str, List[pd.Series]] = defaultdict(list)
            best_point: Point = Point(model=self.model)

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

            self.max_point_list.append(best_point)

        self.concatenated_vars = {key: np.concatenate(val_list) for key, val_list in self.var_lists.items()}

    def plot_variable_pair(self,
                           var1_name: str,
                           var2_name: str) -> None:
        """
        Creates a 2D scatter plot of two variables across all iterations.

        Highlights the global maximum xb point and local maxima for each iteration.

        Args:
            var1_name (str): Name of the first variable (x-axis).
            var2_name (str): Name of the second variable (y-axis).
        """

        var1 = self.var_lists[var1_name]
        var2 = self.var_lists[var2_name]

        num_iters = len(self.var_lists['xb'])
        op = 0.6 / max(num_iters, 1)
        opacity = 0.3

        fig, ax = plt.subplots()
        for i in range(len(self.var_lists['xb'])):
            t = i / len(self.var_lists['xb'])
            cmap = cm.get_cmap("viridis")
            color = cmap(t)
            ax.scatter(var1[i], var2[i], s=15, color=color, alpha=opacity)
            opacity += op

        if not self.max_point_list:
            print(f"No max points found to plot for {var1_name} vs {var2_name}")
            return

        maximum = max(self.max_point_list)
        max_point_1 = maximum.get_val(var1_name)
        max_point_2 = maximum.get_val(var2_name)
        for i, point in enumerate(self.max_point_list):
            point1 = point.get_val(var1_name)
            point2 = point.get_val(var2_name)
            if point != maximum:
                ax.scatter(point1, point2, s=25, color="orange", alpha=0.8, marker="*")

        ax.scatter(max_point_1, max_point_2, s=60, color="red", alpha=0.999, marker="*")
        ax.set_title(f"{var1_name} vs {var2_name}")
        ax.set_xlabel(var1_name)
        ax.set_ylabel(var2_name)
        fig.savefig(os.path.join(self.output_dir, f"scan_{var1_name}_vs_{var2_name}.png"))
        plt.close()

    def make_scan_plots(self) -> None:
        """
        Generates and saves 2D scatter plots for all unique parameter pairs.

        Iterates over all combinations of variable pairs, including xb, and
        plots how the sampled points evolve across iterations.
        """

        print("Making scan plots for", self.model.name, self.decay, self.model.mass_string)
        for var1, var2 in combinations(self.var_names, 2):
            self.plot_variable_pair(var1, var2)

    def plot_max_xb_heatmap(self,
                            var1_name: str,
                            var2_name: str,
                            num_bins: int = 100) -> None:
        """
        Plots a 2D heatmap showing the maximum xb in each bin of two variables.

        Args:
            var1_name (str): Name of the first variable (x-axis).
            var2_name (str): Name of the second variable (y-axis).
            num_bins (int, optional): Number of bins along each axis. Defaults to 100.
        """

        df_comb = pd.DataFrame({key: self.concatenated_vars[key] for key in (var1_name, var2_name, 'xb')})

        # Bin the variables
        df_comb[f'{var1_name}_bin'] = pd.cut(df_comb[var1_name], bins=num_bins, labels=False)
        df_comb[f'{var2_name}_bin'] = pd.cut(df_comb[var2_name], bins=num_bins, labels=False)

        # Group by binned values and compute max xb
        max_xb_in_bins = df_comb.groupby([f'{var1_name}_bin', f'{var2_name}_bin'])['xb'].max().unstack()

        # Plot the heatmap
        fig, ax = plt.subplots(figsize=(10, 8))
        im = ax.imshow(max_xb_in_bins.T,
                       origin='lower',
                       aspect='auto',
                       extent=(
                           float(df_comb[var1_name].min()), float(df_comb[var1_name].max()),
                           float(df_comb[var2_name].min()), float(df_comb[var2_name].max())
                           ),
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
        Generates 2D heatmaps of maximum xb for all variable pairs (excluding xb).

        For each pair of parameters, plots the binned maximum xb values using
        a shared color scale to highlight regions of interest.
        """

        print("Making max XB plots for", self.model.name, self.decay, self.model.mass_string)
        for var1, var2 in combinations(self.var_names, 2):
            if 'xb' not in (var1, var2):
                self.plot_max_xb_heatmap(var1, var2)
