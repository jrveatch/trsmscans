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
from utils.plot_utils import interpolate_grid, mass_label, xb_label

XRES = 200
SRES = 200

def plot_combination(model :str,
                     decay: str,
                     identifier: str,
                     plot_limits: bool,
                     include_sigma_bands: bool = True,
                     log_x: bool = False,
                     log_y: bool = False) -> None:

    # Combination .tsv file name
    input_file_name = os.path.join(env.output_dir(),
                                   model,
                                   "combination",
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
    plot_interpolation(X_mass=X_mass_xb_i,
                       S_mass=S_mass_xb_i,
                       xb=xb_max_i,
                       file_name=output_filename_xbmax,
                       limit_type="max",
                       log_x=log_x,
                       log_y=log_y)

    # Stop here if we are not plotting limits
    if not plot_limits:
        return

    # Load the expected and observed limits
    #X_mass, S_mass, obs_limits, exp_limits = load_limit_data(decay=decay,
    #                                                         identifier=identifier)
    limit_data = load_limit_data(decay=decay,
                                 identifier=identifier)

    # Get the interpolated grids
    X_mass_i, S_mass_i, obs_limits_i = interpolate_grid(limit_data.X_mass,
                                                        limit_data.S_mass,
                                                        limit_data.observed,
                                                        resolution=(XRES, SRES))

    _, _, exp_limits_i = interpolate_grid(limit_data.X_mass,
                                          limit_data.S_mass,
                                          limit_data.expected,
                                          resolution=(XRES, SRES))

    # Align limits to xb_max subset points
    obs_matched = match_limit_values_to_subset(X_mass_xb,
                                               S_mass_xb,
                                               limit_data.X_mass,
                                               limit_data.S_mass,
                                               limit_data.observed)

    exp_matched = match_limit_values_to_subset(X_mass_xb,
                                               S_mass_xb,
                                               limit_data.X_mass,
                                               limit_data.S_mass,
                                               limit_data.expected)

    exp_m1_matched = match_limit_values_to_subset(X_mass_xb,
                                                  S_mass_xb,
                                                  limit_data.X_mass,
                                                  limit_data.S_mass,
                                                  limit_data.expected_m1)

    exp_p1_matched = match_limit_values_to_subset(X_mass_xb,
                                                  S_mass_xb,
                                                  limit_data.X_mass,
                                                  limit_data.S_mass,
                                                  limit_data.expected_p1)

    exp_m2_matched = match_limit_values_to_subset(X_mass_xb,
                                                  S_mass_xb,
                                                  limit_data.X_mass,
                                                  limit_data.S_mass,
                                                  limit_data.expected_m2)

    exp_p2_matched = match_limit_values_to_subset(X_mass_xb,
                                                  S_mass_xb,
                                                  limit_data.X_mass,
                                                  limit_data.S_mass,
                                                  limit_data.expected_p2)

    # Create binary masks: where xb_max exceeds limits
    mask_obs_raw = xb_max > obs_matched
    mask_exp_raw = xb_max > exp_matched
    mask_exp_m1_raw = xb_max > exp_m1_matched
    mask_exp_p1_raw = xb_max > exp_p1_matched
    mask_exp_m2_raw = xb_max > exp_m2_matched
    mask_exp_p2_raw = xb_max > exp_p2_matched

    # Optional: Print summary
    print(f"Observed: {np.sum(mask_obs_raw)} / {len(mask_obs_raw)} points exceed limits")
    if include_sigma_bands:
        print(f"Expected -2σ: {np.sum(mask_exp_m2_raw)} / {len(mask_exp_m2_raw)} points exceed limits")
        print(f"Expected -1σ: {np.sum(mask_exp_m1_raw)} / {len(mask_exp_m1_raw)} points exceed limits")
    print(f"Expected med: {np.sum(mask_exp_raw)} / {len(mask_exp_raw)} points exceed limits")
    if include_sigma_bands:
        print(f"Expected +1σ: {np.sum(mask_exp_p1_raw)} / {len(mask_exp_p1_raw)} points exceed limits")
        print(f"Expected +2σ: {np.sum(mask_exp_p2_raw)} / {len(mask_exp_p2_raw)} points exceed limits")

    # Interpolate the masks to the grid
    limit_interpolation_method: str = 'cubic'
    mask_obs_i = griddata((X_mass_xb, S_mass_xb),
                          mask_obs_raw.astype(float),
                          (X_mass_i, S_mass_i),
                          method=limit_interpolation_method)

    mask_exp_i = griddata((X_mass_xb, S_mass_xb),
                          mask_exp_raw.astype(float),
                          (X_mass_i, S_mass_i),
                          method=limit_interpolation_method)

    mask_exp_m1_i = griddata((X_mass_xb, S_mass_xb),
                             mask_exp_m1_raw.astype(float),
                             (X_mass_i, S_mass_i),
                             method=limit_interpolation_method)

    mask_exp_p1_i = griddata((X_mass_xb, S_mass_xb),
                             mask_exp_p1_raw.astype(float),
                             (X_mass_i, S_mass_i),
                             method=limit_interpolation_method)

    mask_exp_m2_i = griddata((X_mass_xb, S_mass_xb),
                             mask_exp_m2_raw.astype(float),
                             (X_mass_i, S_mass_i),
                             method=limit_interpolation_method)

    mask_exp_p2_i = griddata((X_mass_xb, S_mass_xb),
                             mask_exp_p2_raw.astype(float),
                             (X_mass_i, S_mass_i),
                             method=limit_interpolation_method)

    # Make lists of exclusion masks
    observed_exclusion_masks = [
        {
            "mask": mask_obs_i,  # interpolated 2D array (float)
            "label": "TRSM",
            "style": {"color": "red", "linestyle": "-"}
        }
    ]
    expected_exclusion_masks = [
        {
            "mask": mask_exp_m2_i,  # interpolated 2D array (float)
            "label": r"$-2\sigma$",
            "style": {"color": "purple", "linestyle": ":"}
        },
        {
            "mask": mask_exp_m1_i,  # interpolated 2D array (float)
            "label": r"$-1\sigma$",
            "style": {"color": "purple", "linestyle": "-."}
        },
        {
            "mask": mask_exp_i,  # interpolated 2D array (float)
            "label": "Median",
            "style": {"color": "red", "linestyle": "-"}
        },
        {
            "mask": mask_exp_p1_i,  # interpolated 2D array (float)
            "label": r"$+1\sigma$",
            "style": {"color": "orange", "linestyle": "-."}
        },
        {
            "mask": mask_exp_p2_i,  # interpolated 2D array (float)
            "label": r"$+2\sigma$",
            "style": {"color": "orange", "linestyle": ":"}
        }
    ]

    if not include_sigma_bands:
        # Keep only the median entry (index 2)
        expected_exclusion_masks = [expected_exclusion_masks[2]]

    # Plot the interpolated grid
    plot_interpolation(X_mass=X_mass_i,
                       S_mass=S_mass_i,
                       xb=obs_limits_i,
                       file_name=output_filename_obs,
                       limit_type="observed",
                       contour_masks=observed_exclusion_masks,
                       log_x=log_x,
                       log_y=log_y)

    plot_interpolation(X_mass=X_mass_i,
                       S_mass=S_mass_i,
                       xb=exp_limits_i,
                       file_name=output_filename_exp,
                       limit_type="expected",
                       contour_masks=expected_exclusion_masks,
                       log_x=log_x,
                       log_y=log_y)

def plot_interpolation(X_mass: np.ndarray,
                       S_mass: np.ndarray,
                       xb: np.ndarray,
                       file_name: str,
                       limit_type: str,
                       contour_masks: Optional[List[Dict]] = None,
                       log_x: bool = False,
                       log_y: bool = False) -> None:

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
    cbar.set_label(xb_label(limit_type))

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

            style_mpl = {
                "colors": style.get("color"),
                "linestyles": style.get("linestyle")
            }

            try:
                ax.contour(X_mass, S_mass, mask, levels=[0.5], **style_mpl)
            except Exception as e:
                print(f"Failed to draw contour for label '{label}': {e}")

            # Always create a proxy for the legend
            if label:
                ax.plot([], [], label=label,
                        color=style.get("color", "black"),
                        linestyle=style.get("linestyle", "-"))

    ax.set_xlim(X_mass.min(), X_mass.max())
    ax.set_ylim(S_mass.min(), S_mass.max())

    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")

    # Enable legend if any labels are set
    _, labels = ax.get_legend_handles_labels()
    if labels:
        ax.legend()

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
        required_cols = {'XMass', 'SMass', 'xb'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns in TSV file: {missing}")
        
        X_mass = df['XMass'].to_numpy()
        S_mass = df['SMass'].to_numpy()
        xbmax = df['xb'].to_numpy() * 1000 # Convert to fb
        return X_mass, S_mass, xbmax

    except Exception as e:
        raise RuntimeError(f"Failed to read or parse data from {file_path}: {e}")

if __name__ =="__main__":

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Identifier")
    arg_parser.add_argument("-l", "--plot-limits", action="store_true", help="Produce exclusion limits plots")
    arg_parser.add_argument("--no-sigma-bands", action="store_true", help="Do not plot ±1σ and ±2σ expected contours")
    arg_parser.add_argument("--log-x", action="store_true", help="Use logarithmic scale for the X mass axis")
    arg_parser.add_argument("--log-y", action="store_true", help="Use logarithmic scale for the S mass axis")
    arg_parser.add_argument("--log-axes", action="store_true", help="Use logarithmic scale for both axes (equivalent to --log_x --log_y)")
    args = arg_parser.parse_args()

    # If --log_axes is used, override both log_x and log_y
    log_x = args.log_x or args.log_axes
    log_y = args.log_y or args.log_axes

    plot_combination(model = args.model,
                     decay=args.decay,
                     identifier=args.identifier,
                     plot_limits=args.plot_limits,
                     include_sigma_bands=not args.no_sigma_bands,
                     log_x=log_x,
                     log_y=log_y)
