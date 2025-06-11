#!/usr/bin/env python3

import argparse
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from typing import Tuple

import utils.env_utils as env
from utils.mass_json_utils import load_limit_data

def plot_combination(model :str,
                     decay: str,
                     identifier: str,
                     plot_limits: bool) -> None:

    plot_xb_max(model=model, decay=decay, identifier=identifier)
    if plot_limits:
        plot_exclusions(model=model, decay=decay, identifier=identifier)
    
def plot_xb_max(model: str,
                decay: str,
                identifier: str) -> None:

    # Combination .tsv file name
    input_file_name = os.path.join(env.output_dir(),
                                   model,
                                   "scan",
                                   decay,
                                   f"{decay}_{identifier}_combination.tsv")

    # Output directory and filename for the plot
    output_filename = os.path.join(output_directory(model, decay),
                                   f"{decay}_{identifier}_xbmax.png")

    # Load data from the TSV file
    X_mass, S_mass, xb_max = load_data(input_file_name)

    # Plot the interpolated grid
    plot_interpolation(X_mass, S_mass, xb_max, output_filename)

def plot_exclusions(model: str,
                    decay: str,
                    identifier: str) -> None:

    # Output filenames for the plot
    output_filename_obs = os.path.join(output_directory(model, decay), f"{decay}_{identifier}_observed.png")
    output_filename_exp = os.path.join(output_directory(model, decay), f"{decay}_{identifier}_expected.png")

    X_mass, S_mass, obs_limits, exp_limits = load_limit_data(decay=decay,
                                             identifier=identifier)

    # Plot the interpolated grid
    plot_interpolation(X_mass, S_mass, obs_limits, output_filename_obs)
    plot_interpolation(X_mass, S_mass, exp_limits, output_filename_exp)

def plot_interpolation(X_mass: np.ndarray,
                       S_mass: np.ndarray,
                       xb_max: np.ndarray,
                       file_name: str) -> None:

    # Get the interpolated grid
    X_mass_i, S_mass_i, xb_max_i = interpolate_grid(X_mass, S_mass, xb_max, resolution=(200, 200))

        # Create the plot
    fig, ax = plt.subplots()
    contour = ax.contourf(X_mass_i,
                          S_mass_i,
                          xb_max_i,
                          levels=30,
                          norm=mcolors.LogNorm(),
                          cmap='viridis')

    ax.set_xlim(X_mass.min(), X_mass.max())
    ax.set_ylim(S_mass.min(), S_mass.max())

    ax.set_xlabel(mass_label("X"))
    ax.set_ylabel(mass_label("S"))

    cbar = plt.colorbar(contour)
    cbar.set_label(xb_max_label())

    fig.tight_layout()
    fig.savefig(file_name)

def output_directory(model: str,
                     decay: str) -> str:
    """
    Returns the output directory for the given model and decay mode.
    Ensures the directory exists by creating it if necessary.
    
    Args:
        model (str): The name of the theoretical model.
        decay (str): The decay mode.
    
    Returns:
        str: The path to the output directory.
    """
    out_dir = os.path.join(env.output_dir(), model, "plots", decay, "combination")

    # Ensure the output directory exists
    os.makedirs(out_dir, exist_ok=True)

    return out_dir

def xb_max_label() -> str:
    """
    Returns the label for the xb_max plot.
    
    Returns:
        str: The label for the xb_max plot.
    """
    return r"Max $\sigma\times BR$ [fb]"

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
        
        X_mass = df['XMass'].to_numpy()
        S_mass = df['SMass'].to_numpy()
        xbmax = df['xbmax'].to_numpy() * 1000 # Convert to fb
        return X_mass, S_mass, xbmax

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
    arg_parser.add_argument("-l", "--plot_limits", action="store_true", help="Produce exclusion limits plots")
    args = arg_parser.parse_args()

    plot_combination(model = args.model,
                     decay=args.decay,
                     identifier=args.identifier,
                     plot_limits=args.plot_limits)
