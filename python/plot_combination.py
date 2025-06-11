#!/usr/bin/env python3

import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from typing import Tuple

from utils.env_utils import output_dir

def plot_combination(model :str,
                     decay: str,
                     identifier: str) -> None:

    plot_xb_max(model=model, decay=decay, identifier=identifier)
    
def plot_xb_max(model: str,
                decay: str,
                identifier: str) -> None:

    # Combination .tsv file name
    input_file_name = os.path.join(output_dir(), model, "scan", decay, f"{decay}_{identifier}_combination.tsv")

    # Load data from the TSV file
    x_values, y_values, z_values = load_data(input_file_name)

    # Get the interpolated grid
    Xi, Yi, Zi = interpolate_grid(x_values, y_values, z_values, resolution=(200, 200))

    # Create the plot
    fig, ax = plt.subplots()
    contour = ax.contourf(Xi, Yi, Zi, levels=30, norm=mcolors.LogNorm(), cmap='viridis')

    ax.set_xlim(x_values.min(), x_values.max())
    ax.set_ylim(y_values.min(), y_values.max())

    ax.set_xlabel(mass_label("X"))
    ax.set_ylabel(mass_label("S"))

    cbar = plt.colorbar(contour)
    cbar.set_label(xb_max_label())

    output_directory = os.path.join(output_dir(), model, "plots", decay, "combination")
    output_filename = os.path.join(output_directory, f"{decay}_{identifier}_combination.png")
    os.makedirs(output_directory, exist_ok=True)
    fig.tight_layout()
    fig.savefig(output_filename)

def xb_max_label() -> str:
    """
    Returns the label for the xb_max plot.
    
    Returns:
        str: The label for the xb_max plot.
    """
    return r"Max $\sigma\times BR$ [pb]"

def mass_label(particle: str) -> str:
    """
    Returns the label for the mass plot.
    
    Returns:
        str: The label for the mass plot.
    """
    return fr"$m_{{{particle}}}$ [GeV]"

def load_data(file_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Load XMass, SMass, and MaxXB from a TSV file using column names.

    Args:
        file_path (str): Path to the TSV file.

    Returns:
        tuple: Three numpy arrays containing XMass, SMass, and MaxXB.

    Raises:
        RuntimeError: If the file cannot be read or parsed correctly.
    """
    try:
        df = pd.read_csv(file_path, sep='\t')
        required_cols = {'XMass', 'SMass', 'xbmax'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns in TSV file: {missing}")
        
        x = df['XMass'].to_numpy()
        y = df['SMass'].to_numpy()
        z = df['xbmax'].to_numpy()
        return x, y, z

    except Exception as e:
        raise RuntimeError(f"Failed to read or parse data from {file_path}: {e}")

def interpolate_grid(x: np.ndarray,
                     y: np.ndarray,
                     z: np.ndarray, 
                     resolution: Tuple[int, int]=(200, 200)
                    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create interpolated 2D grid from scattered data points.

    Args:
        x (np.ndarray): 1D array of x-coordinates.
        y (np.ndarray): 1D array of y-coordinates.
        z (np.ndarray): 1D array of values at the (x, y) coordinates.
        resolution (tuple[int, int]): Resolution of the output grid.

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Meshgrid arrays (Xi, Yi) and interpolated values (Zi).
    """
    xi = np.linspace(x.min(), x.max(), resolution[0])
    yi = np.linspace(y.min(), y.max(), resolution[1])
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = griddata((x, y), z, (Xi, Yi), method='linear')
    return Xi, Yi, Zi

if __name__ =="__main__":

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Identifier")
    args = arg_parser.parse_args()

    plot_combination(model = args.model,
                     decay=args.decay,
                     identifier=args.identifier)
