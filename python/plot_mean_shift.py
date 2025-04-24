
import matplotlib
import matplotlib.lines
import os

import pandas as pd

from utils.file_utils import plots_dir

import matplotlib.pyplot as plt

from utils.model import Model

class MeanShiftPlotter:
    """
    Class to plot the results of the mean shift algorithm.
    """

    def __init__(self,
                 model: Model,
                 decay: str):
        self.model = model
        self.decay = decay

        # Set output directory for plots
        self.out_dir = plots_dir()

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
    pass