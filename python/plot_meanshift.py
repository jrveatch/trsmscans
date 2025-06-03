#!/usr/bin/env python3

"""
Generates 2D plots for visualizing the paths taken by the mean-shift optimizer.

This module loads walk files generated during mean-shift scans and creates plots
that show how optimization paths evolve in parameter space, optionally colored
by cross section times branching ratio (xb) or other metrics.
"""

import argparse
from itertools import combinations
import os
from typing import Any, cast, Sequence

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
from matplotlib.colors import Normalize
import numpy as np
import pandas as pd

from utils.file_utils import plots_dir, scan_dir
from utils.model import Model

class MeanShiftPlotter:
    """
    Class to plot the results of the mean shift algorithm.

    Loads scan results from walk files and generates 2D plots of parameter
    space walks, with color indicating xb or other selected variables.
    """

    def __init__(self,
                 model: Model,
                 decay: str):
        """
        Initializes the plotter for a specific model and decay mode.

        Args:
            model (Model): The scalar model associated with the scan.
            decay (str): The decay channel used in the scan.
        """

        self.model = model
        self.decay = decay

        # Set and create output directory for plots
        self.out_dir = os.path.join(plots_dir(model=self.model, decay=self.decay),"meanshift")
        os.makedirs(self.out_dir, exist_ok=True)

        self.walk_data = pd.DataFrame()
        self.load_data()

    def parse_optimizer_id(self,
                           filename: str) -> str:
        """
        Extracts the optimizer identifier from a walk file's filename.

        Args:
            filename (str): Name of the file.

        Returns:
            str: Parsed optimizer identifier.
        """
        return filename.split('_')[1]

    def load_data(self) -> None:
        """
        Loads walk file data into a single pandas DataFrame.

        This method scans the walk directory for `.tsv` files, loads each into a
        DataFrame, and combines them into a single DataFrame stored in `self.walk_data`.
        """
        data_dir = os.path.join(scan_dir(model=self.model, decay=self.decay),"meanshift","walk")

        # List of individual DataFrames from each file
        walk_data_rows = []

        # Loop over .tsv files and build a list of DataFrames
        for filename in sorted(os.listdir(data_dir)):
            if not filename.endswith(".tsv"):
                continue
            path = os.path.join(data_dir,filename)
            try:
                optimizer_id = self.parse_optimizer_id(filename)
                walk_id = os.path.splitext(filename)[0]
                # Get walk type from file name and skip if it is unknown
                walk_type = "pos" if "walk_pos_" in filename else "max" if "walk_max_" in filename else "unknown"
                if walk_type == "unknown":
                    print(f"Skipping unrecognized walk file: {filename}")
                    continue
                df = pd.read_csv(path, sep="\t")
                df['optimizer_id'] = optimizer_id
                df['walk_id'] = walk_id
                df['walk_type'] = walk_type
                walk_data_rows.append(df)
            except Exception as e:
                print(f"Error loading {path}: {e}")

        # Raise an error if no data is loaded
        if not walk_data_rows:
            raise ValueError(f"No .tsv files found in {data_dir}")

        # Combine all into one long DataFrame
        valid_rows = [df for df in walk_data_rows if not df.empty and not df.isna().all().all()]
        self.walk_data = pd.concat(valid_rows, ignore_index=True)

    def plot_paths_2d(self,
                      x: str,
                      y: str,
                      color_by: str = "xb",
                      walk_type: str = "pos",
                      save=False,
                      show=True) -> None:
        """
        Plots 2D paths in parameter space for each optimizer.

        Each path is drawn as a line with a gradient color representing a metric
        (by default, xb). Plots can be saved or displayed interactively.

        Args:
            x (str): Column name to use for the x-axis.
            y (str): Column name to use for the y-axis.
            color_by (str): Column to use for coloring the paths (default: "xb").
            save (bool): Whether to save the plot to file.
            show (bool): Whether to display the plot in a window.
        """

        data = self.walk_data[self.walk_data["walk_type"] == walk_type]
        if data.empty:
            print(f"No data to plot for walk type: {walk_type}")
            return

        fig, ax = plt.subplots(figsize=(8, 6))

        # Normalize the color scale across all values
        all_values = data[color_by].values
        norm = Normalize(all_values.min(), all_values.max())
        cmap = plt.get_cmap("viridis")

        # Plot each optimizer path as a colored segment collection
        for walk_id, group in data.groupby("walk_id"):
            x_vals = group[x].values
            y_vals = group[y].values
            colors = group[color_by].values

            if len(x_vals) < 2:
                continue  # Can't form a line

            # Create line segments between each pair of points
            points = np.array([x_vals, y_vals]).T.reshape(-1, 1, 2)
            segments_array = np.concatenate([points[:-1], points[1:]], axis=1)

            # Cast to help Pyright recognize it
            segments = cast(Sequence[Any], segments_array)

            # Use segment-wise color (last point is not used in a segment)
            lc = LineCollection(segments, cmap=cmap, norm=norm)
            lc.set_array(np.asarray(colors[:-1])) # one color per segment
            lc.set_linewidth(2)
            ax.add_collection(lc)

        ax.set_xlabel(x)
        ax.set_ylabel(y)
        ax.set_title(f"Mean Shift Walks: {x} vs {y}")
        ax.autoscale()
        ax.set_aspect('auto')

        # Add a shared colorbar
        sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
        sm.set_array([])  # Only needed for the colorbar
        fig.colorbar(sm, ax=ax, label=color_by)

        plt.tight_layout()

        if save:
            filename = f"meanshift_{walk_type}_path_gradient_{x}_vs_{y}.png"
            filepath = os.path.join(self.out_dir, filename)
            plt.savefig(filepath, dpi=300)

        if show:
            plt.show()
        else:
            plt.close()

    def make_mean_shift_plots(self) -> None:
        """
        Generates and saves 2D mean-shift path plots for all parameters.

        Creates xb vs. parameter plots and parameter vs. parameter pairwise plots.
        """
        for walk_type in ["pos", "max"]:
            print(f"Generating plots for walk type: {walk_type}")
            for param in self.model.input_parameter_names:
                self.plot_paths_2d(x=param, y="xb", walk_type=walk_type, save=True, show=False)
            for pair in combinations(self.model.input_parameter_names, 2):
                self.plot_paths_2d(x=pair[0], y=pair[1], walk_type=walk_type, save=True, show=False)

# Command-line interface to generate mean-shift path plots.
# Creates a MeanShiftPlotter and produces 2D visualizations of the optimization walks.
if __name__ == '__main__':
    
    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    plotter = MeanShiftPlotter(model=model,
                               decay=args.decay)

    plotter.make_mean_shift_plots()
