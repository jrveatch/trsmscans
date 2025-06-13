#!/usr/bin/env python3

import argparse
from math import exp
import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import LogLocator, LogFormatterMathtext
import numpy as np
import pandas as pd
from scipy.interpolate import griddata
from typing import Dict, List, Optional, Tuple

import utils.env_utils as env
from mass_grid.mass_json_utils import load_limit_data

XRES = 200
SRES = 200

def plot_combination(model :str,
                     decay: str,
                     identifier: str,
                     plot_limits: bool) -> None:

    # Combination .tsv file name
    input_file_name = os.path.join(env.output_dir(),
                                   model,
                                   "scan",
                                   decay,
                                   f"{decay}_{identifier}_combination.tsv")

    # Output filenames for the plot
    output_filename_xbmax = os.path.join(output_directory(model, decay), f"{decay}_{identifier}_xbmax.png")
    output_filename_obs = os.path.join(output_directory(model, decay), f"{decay}_{identifier}_observed.png")
    output_filename_exp = os.path.join(output_directory(model, decay), f"{decay}_{identifier}_expected.png")

    # Load xbmax data from the TSV file
    X_mass_xb, S_mass_xb, xb_max = load_data(input_file_name)

    # Get the interpolated grid for xbmax
    X_mass_xb_i, S_mass_xb_i, xb_max_i = interpolate_grid(X_mass_xb, S_mass_xb, xb_max, resolution=(XRES, SRES))

    # Plot the xbmax interpolated grid
    plot_interpolation(X_mass_xb_i, S_mass_xb_i, xb_max_i, output_filename_xbmax)

    # Stop here if we are not plotting limits
    if not plot_limits:
        return

    # Load the expected and observed limits
    X_mass, S_mass, obs_limits, exp_limits = load_limit_data(decay=decay,
                                                             identifier=identifier)

    # Get the interpolated grids
    X_mass_i, S_mass_i, obs_limits_i = interpolate_grid(X_mass, S_mass, obs_limits, resolution=(XRES, SRES))
    _, _, exp_limits_i = interpolate_grid(X_mass, S_mass, exp_limits, resolution=(XRES, SRES))

    # Align limits to xb_max subset points
    obs_matched = match_limit_values_to_subset(X_mass_xb, S_mass_xb, X_mass, S_mass, obs_limits)
    exp_matched = match_limit_values_to_subset(X_mass_xb, S_mass_xb, X_mass, S_mass, exp_limits)

    # Create binary masks: where xb_max exceeds limits
    mask_obs_raw = xb_max > obs_matched
    mask_exp_raw = xb_max > exp_matched

    # Optional: Print summary
    print(f"Observed mask: {np.sum(mask_obs_raw)} / {len(mask_obs_raw)} points exceed limits")
    print(f"Expected mask: {np.sum(mask_exp_raw)} / {len(mask_exp_raw)} points exceed limits")

    # Interpolate the masks to the grid
    mask_obs_i = griddata((X_mass_xb, S_mass_xb),
                          mask_obs_raw.astype(float),
                          (X_mass_i, S_mass_i),
                          method='cubic')
    mask_exp_i = griddata((X_mass_xb, S_mass_xb),
                          mask_exp_raw.astype(float),
                          (X_mass_i, S_mass_i),
                          method='cubic')

    # Make lists of exclusion masks
    observed_exclusion_mask = [
        {
            "mask": mask_obs_i,  # interpolated 2D array (float)
            "label": "TRSM",
            "style": {"color": "red", "linestyle": "-"}
        }
    ]
    expected_exclusion_mask = [
        {
            "mask": mask_exp_i,  # interpolated 2D array (float)
            "label": "Median",
            "style": {"color": "red", "linestyle": "-"}
        }
    ]

    # TODO: Plot the exclusion masks as contours on the limits plots

    # Plot the interpolated grid
    plot_interpolation(X_mass_i, S_mass_i, obs_limits_i, output_filename_obs, observed_exclusion_mask)
    plot_interpolation(X_mass_i, S_mass_i, exp_limits_i, output_filename_exp, expected_exclusion_mask)

def plot_interpolation(X_mass: np.ndarray,
                       S_mass: np.ndarray,
                       xb: np.ndarray,
                       file_name: str,
                       contour_masks: Optional[List[Dict]] = None) -> None:

        # Create the plot
    fig, ax = plt.subplots()
    contour = ax.contourf(X_mass,
                          S_mass,
                          xb,
                          levels=np.logspace(np.log10(np.nanmin(xb)), np.log10(np.nanmax(xb)), 200),
                          norm=mcolors.LogNorm(),
                          cmap='viridis')

    ax.set_xlim(X_mass.min(), X_mass.max())
    ax.set_ylim(S_mass.min(), S_mass.max())

    ax.set_xlabel(mass_label("X"))
    ax.set_ylabel(mass_label("S"))

    cbar = plt.colorbar(contour)
    cbar.set_label(xb_label("Max"))

    # Set colorbar ticks at powers of 10
    cbar.locator = LogLocator(base=10.0, numticks=10)
    cbar.formatter = LogFormatterMathtext(base=10.0)
    cbar.update_ticks()

    # ➕ Add contour overlays for masks
    if contour_masks:
        for entry in contour_masks:
            mask = entry.get("mask")
            label = entry.get("label", None)
            style = entry.get("style", {})

            # Translate style keys for matplotlib.contour
            style_mpl = {
                "colors": style.get("color"),
                "linestyles": style.get("linestyle")
            }

            # Contour at mask threshold 0.5 (float-valued mask)
            cs = ax.contour(X_mass, S_mass, mask, levels=[0.5], **style_mpl)

            # Only set label if contour is drawn
            #if label and cs.collections:
            #    cs.collections[0].set_label(label)

    # Enable legend if any labels are present
    #if contour_masks and any(e.get("label") for e in contour_masks):
    #    ax.legend()

    fig.tight_layout()
    fig.savefig(file_name)

def match_limit_values_to_subset(X_sub: np.ndarray,
                                 S_sub: np.ndarray,
                                 X_all: np.ndarray,
                                 S_all: np.ndarray,
                                 limit_values: np.ndarray) -> np.ndarray:
    """
    Given a subset of points (X_sub, S_sub) and a full limit grid (X_all, S_all),
    return the corresponding limit values for the subset.

    Args:
        X_sub, S_sub: Points in the xb_max dataset
        X_all, S_all: Full coordinate grid from limit dataset
        limit_values: Limit values on the full grid

    Returns:
        np.ndarray of limit values matching the subset coordinates
    """
    lookup = {(x, s): val for x, s, val in zip(X_all, S_all, limit_values)}
    try:
        return np.array([lookup[(x, s)] for x, s in zip(X_sub, S_sub)])
    except KeyError as e:
        raise ValueError(f"Subset point {e} not found in limit dataset.")

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

def xb_label(prefix: str) -> str:
    """
    Returns the label for the interpolated plot.

    Args:
        prefix (str): The prefix for the label, e.g., "Max".

    Returns:
        str: The label for the interpolated plot.
    """
    return fr"{prefix} $\sigma\times BR$ [fb]"

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
