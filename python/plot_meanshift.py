#!/usr/bin/env python3

import argparse
import matplotlib
import matplotlib.lines
import os

import matplotlib.pyplot as plt
from matplotlib.collections import LineCollection
import numpy as np
import pandas as pd

from utils.file_utils import plots_dir, scan_dir
from utils.model import Model

class MeanShiftPlotter:
    """
    Class to plot the results of the mean shift algorithm
    """

    def __init__(self,
                 model: Model,
                 decay: str):

        self.model = model
        self.decay = decay

        # Set and create output directory for plots
        self.out_dir = os.path.join(plots_dir(model=self.model, decay=self.decay),"meanshift")
        os.makedirs(self.out_dir, exist_ok=True)

        self.walk_data = pd.DataFrame()
        self.load_files()

    def parse_optimizer_id(self, filename: str) -> str:
        """Extract the optimizer identifier from the filename."""
        return filename.split('_')[1]

    def load_files(self):
        """Load walk file data into a single pandas DataFrame"""
        data_dir = os.path.join(scan_dir(model=self.model, decay=self.decay),"files","walk")

        # List of individual DataFrames from each file
        walk_data_rows = []

        # Loop over .tsv files and build a list of DataFrames
        for filename in sorted(os.listdir(data_dir)):
            if not filename.endswith(".tsv"):
                continue
            path = os.path.join(data_dir,filename)
            try:
                optimizer_id = self.parse_optimizer_id(filename)
                df = pd.read_csv(path, sep="\t")
                df['optimizer_id'] = optimizer_id
                walk_data_rows.append(df)
            except Exception as e:
                print(f"Error loading {path}: {e}")

        # Raise an error if no data is loaded
        if not walk_data_rows:
            raise ValueError(f"No .tsv files found in {data_dir}")

        # Combine all into one long DataFrame
        valid_rows = [df for df in walk_data_rows if not df.empty and not df.isna().all().all()]
        self.walk_data = pd.concat(valid_rows, ignore_index=True)

    def plot_paths_2d(self, x: str, y: str, color_by: str = "xb", save=False, show=True):
        """
        Plot 2D paths for each optimizer, coloring each path with a gradient based on a column (e.g. xb).
        The color scale is shared across all paths.

        Parameters:
            x (str): X-axis column
            y (str): Y-axis column
            color_by (str): Column used for coloring (default: "xb")
            save (bool): Whether to save the plot
            show (bool): Whether to display the plot
        """
        if self.walk_data.empty:
            print("No data to plot.")
            return

        fig, ax = plt.subplots(figsize=(8, 6))

        # Normalize the color scale across all values
        all_values = self.walk_data[color_by].values
        norm = plt.Normalize(all_values.min(), all_values.max())
        cmap = plt.get_cmap("viridis")

        # Plot each optimizer path as a colored segment collection
        for optimizer, group in self.walk_data.groupby("optimizer_id"):
            x_vals = group[x].values
            y_vals = group[y].values
            colors = group[color_by].values

            if len(x_vals) < 2:
                continue  # Can't form a line

            # Create line segments between each pair of points
            points = np.array([x_vals, y_vals]).T.reshape(-1, 1, 2)
            segments = np.concatenate([points[:-1], points[1:]], axis=1)

            # Use segment-wise color (except last point which has no next point)
            lc = LineCollection(segments, cmap=cmap, norm=norm)
            lc.set_array(colors[:-1])  # one color per segment
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
        cbar = fig.colorbar(sm, ax=ax)
        cbar.set_label(color_by)

        plt.tight_layout()

        if save:
            filename = f"meanshift_path_gradient_{x}_vs_{y}.png"
            filepath = os.path.join(self.out_dir, filename)
            plt.savefig(filepath, dpi=300)
            print(f"Plot saved to: {filepath}")

        if show:
            plt.show()
        else:
            plt.close()

    def make_mean_shift_plots(self):
        self.plot_paths_2d(x="thetaHS",y="xb",save=True,show=False)
        pass

def __generate_visualizations(self):

    # Initialize plot path        
    plot_path = plots_dir(
            model = self.model,
            decay = self.decay
    )

    # Create plots dir
    os.makedirs(plot_path, exist_ok=True)

    walk_tsv = f"{self.out_dir}files/tsv/{self.__label}_meanshift_walk.tsv"

    df = pd.read_csv(walk_tsv, sep="\t")

    # Create param plots
    for i in range(len(self.local_param_space.parameter_names)):
        for j in range(i, len(self.local_param_space.parameter_names)):
            x_label = self.local_param_space.parameter_names[i]
            y_label = self.local_param_space.parameter_names[j]

            plt.plot(df[x_label], df[y_label])
            plt.plot(df[x_label].iloc[-1], df[y_label].iloc[-1], marker="*")

            plt.xlabel(x_label)
            plt.ylabel(y_label)
            # plt.scatter(X, Y)
            plt.savefig(f"{plot_path}{self.local_param_space.model_name}_lines_{self.__label}_{x_label}_{y_label}.jpg", format="JPEG")
            plt.cla()
            plt.clf()

    # Create time series
    for parname in self.local_param_space.parameter_names:
        plt.plot(df["iter"], df[parname], c="tab:blue", label=parname)
        plt.xlabel("iter")
        plt.ylabel(parname)
        ax2 = plt.gca().twinx()
        ax2.plot(df["iter"], df["max_xb"], c="tab:red", label="max xb")
        ax2.plot(df["iter"], df["avg_xb"], c="tab:orange", label="average xb")
        ax2.set_ylabel("xb")
        param_man = matplotlib.lines.Line2D([0], [0], c="tab:blue", label=parname)
        handles, labels = plt.gca().get_legend_handles_labels()
        handles.extend([param_man])
        labels.extend([parname])
        handles.reverse()
        labels.reverse()
        plt.legend(handles = handles, labels = labels, loc = "lower right", )
        plt.savefig(f"{plot_path}{self.local_param_space.model_name}_timeseries_iter_{self.__label}_{parname}_xb.jpg", format="JPEG")
        plt.cla()
        plt.clf()

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
