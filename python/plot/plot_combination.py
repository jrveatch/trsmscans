#!/usr/bin/env python3

import os
import matplotlib.pyplot as plt
import matplotlib.colors as mcolors
from matplotlib.ticker import LogLocator, LogFormatterMathtext
from matplotlib.colors import BoundaryNorm
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd
from typing import Dict, List, Literal, Optional, Tuple

import utils.env_utils as env
from mass_grid.mass_json_utils import load_limit_data
from plot.plot_utils import interpolate_grid, mass_label, xb_label
from plot.plot_utils import get_discrete_colors, match_limit_values_to_subset
from utils.precision_utils import Precision

class CombinationPlotter:
    """
    Generates scan summary plots from combined scalar model data.

    This includes:
    - An interpolated xbmax heatmap
    - Expected and observed exclusion contours
    - xb/limit ratio maps

    Attributes:
        model (str): The scalar model name.
        decay (str): The decay channel.
        identifier (str): Mass grid identifier used to locate the .tsv.
        plot_limits (bool): Whether to overlay exclusion contours.
        include_sigma_bands (bool): If True, adds ±1σ and ±2σ expected bands.
        log_x (bool): Apply log scale to x-axis.
        log_y (bool): Apply log scale to y-axis.
    """
    def __init__(self,
                 model: str,
                 decay: str,
                 identifier: str,
                 plot_limits: bool = True,
                 include_sigma_bands: bool = True,
                 log_x: bool = False,
                 log_y: bool = False):
        """
        Initialize the CombinationPlotter.

        Args:
            model (str): Model name.
            decay (str): Decay mode.
            identifier (str): Mass set identifier (used to locate combined scan file).
            plot_limits (bool): Whether to overlay exclusion contours.
            include_sigma_bands (bool): Whether to include ±1σ and ±2σ contours.
            log_x (bool): Log scale for x-axis (X mass).
            log_y (bool): Log scale for y-axis (S mass).
        """

        self.model = model
        self.decay = decay
        self.identifier = identifier
        self.plot_limits = plot_limits
        self.include_sigma_bands = include_sigma_bands
        self.log_x = log_x
        self.log_y = log_y

        self.output_dir = self.get_output_dir()
        self.xres = 200
        self.sres = 200

        self.input_file = os.path.join(env.output_dir(),
                                       self.model,
                                       "combination",
                                       f"{self.decay}_{self.identifier}_combination.tsv")

        self.X_mass_xb, self.S_mass_xb, self.xb_max, self.precision_values = load_data(self.input_file)

    def get_output_dir(self) -> str:
        """
        Construct and return the output directory for plots.
        
        Returns:
            str: The path to the output directory.
        """
        path = os.path.join(env.output_dir(), self.model, "plots", self.decay, "combination")
        os.makedirs(path, exist_ok=True)
        return path

    def make_combination_plots(self) -> None:
        """
        Generate all plots: xbmax, expected, observed, and xb/limit ratio.
        """

        # Interpolated grid for xb max
        Xi, Yi, Zi = interpolate_grid(x=self.X_mass_xb,
                                      y=self.S_mass_xb,
                                      z=self.xb_max,
                                      resolution=(self.xres, self.sres))

        plot_interpolation(Xi, Yi, Zi,
                           file_name=os.path.join(self.output_dir, f"{self.decay}_{self.identifier}_xbmax.png"),
                           limit_type="max",
                           log_x=self.log_x,
                           log_y=self.log_y)

        if not self.plot_limits:
            return

        # Load limit data
        limits = load_limit_data(decay=self.decay, identifier=self.identifier)

        # Match and interpolate
        matched = {
            name: match_limit_values_to_subset(self.X_mass_xb,
                                               self.S_mass_xb,
                                               limits.X_mass,
                                               limits.S_mass,
                                               getattr(limits, name))
            for name in ["observed", "expected", "expected_m1", "expected_p1", "expected_m2", "expected_p2"]
        }

        masks = {
            name: self.xb_max > matched[name]
            for name in matched
        }

        self.print_summary(masks)

        # Interpolate masks
        interp_masks = {
            name: interpolate_grid(self.X_mass_xb,
                                   self.S_mass_xb,
                                   masks[name].astype(float),
                                   resolution=(self.xres, self.sres))[2]
            for name in masks
        }

        # Build mask configs
        observed_masks, expected_masks = build_contour_mask_sets(interp_masks=interp_masks,
                                                                 include_sigma=self.include_sigma_bands)

        # Plot observed and expected
        Xi_l, Yi_l, obs_i = interpolate_grid(limits.X_mass,
                                             limits.S_mass,
                                             limits.observed,
                                             resolution=(self.xres, self.sres))
        _, _, exp_i = interpolate_grid(limits.X_mass,
                                       limits.S_mass,
                                       limits.expected,
                                       resolution=(self.xres, self.sres))

        plot_interpolation(Xi_l, Yi_l, obs_i,
                           file_name=os.path.join(self.output_dir, f"{self.decay}_{self.identifier}_observed.png"),
                           limit_type="observed",
                           contour_masks=observed_masks,
                           log_x=self.log_x,
                           log_y=self.log_y)

        plot_interpolation(Xi_l, Yi_l, exp_i,
                           file_name=os.path.join(self.output_dir, f"{self.decay}_{self.identifier}_expected.png"),
                           limit_type="expected",
                           contour_masks=expected_masks,
                           log_x=self.log_x,
                           log_y=self.log_y)

        # Plot ratio map
        plot_xb_to_limit_ratio(self.xb_max,
                               matched["observed"],
                               self.X_mass_xb,
                               self.S_mass_xb,
                               file_name=os.path.join(self.output_dir, f"{self.decay}_{self.identifier}_ratio_obs.png"),
                               log_x=self.log_x,
                               log_y=self.log_y)

        # Plot precision map
        self.plot_precision_map()

    def print_summary(self, masks: Dict[str, np.ndarray]) -> None:
        """
        Print how many xb_max values exceed each limit band.

        Args:
            masks (Dict[str, np.ndarray]): Dictionary of raw mask arrays keyed by limit type.
        """
        print(f"Observed: {np.sum(masks['observed'])} / {len(masks['observed'])} points exceed limits")
        
        if self.include_sigma_bands:
            for sigma in ['expected_m2', 'expected_m1']:
                count = np.sum(masks[sigma])
                total = len(masks[sigma])
                label = sigma.replace('expected_', '').replace('m', '-').replace('p', '+') + 'σ'
                print(f"Expected {label}: {count} / {total} points exceed limits")

        count = np.sum(masks['expected'])
        print(f"Expected med: {count} / {len(masks['expected'])} points exceed limits")

        if self.include_sigma_bands:
            for sigma in ['expected_p1', 'expected_p2']:
                count = np.sum(masks[sigma])
                total = len(masks[sigma])
                label = sigma.replace('expected_', '').replace('m', '-').replace('p', '+') + 'σ'
                print(f"Expected {label}: {count} / {total} points exceed limits")

    def plot_precision_map(self) -> None:
        """
        Plot a categorized map of the precision levels used in the scan.
        """

        # Replace MISSING precision values with NaN to leave them out of plot
        precision_values = self.precision_values.astype(float)  # make it float to support NaN
        precision_values[self.precision_values == Precision.MISSING.value] = np.nan

        # Interpolate from scan points to grid
        Xi, Yi, Pi = interpolate_grid(
            self.X_mass_xb,
            self.S_mass_xb,
            precision_values,  # array of enum values
            resolution=(self.xres, self.sres),
            method='linear'
        )

        # Add epsilon to precision values to avoid bin-edge issues
        epsilon = 0.01
        Pi = np.round(Pi) + epsilon

        # All enum levels
        precision_levels = [p for p in Precision if p != Precision.MISSING]

        # Define boundaries based on enum values
        levels = [p.value for p in precision_levels]
        levels.append(levels[-1] + 1)  # upper edge for last bin

        # Labels using str(p) → already lowercase
        labels = [str(p).capitalize() for p in precision_levels]

        # Colors: 1 per bin
        num_bins = len(levels) - 1
        colors = get_discrete_colors(num_bins,
                                     cmap_name="plasma")

        cmap = mcolors.ListedColormap(colors)
        norm = BoundaryNorm(levels,
                            ncolors=num_bins,
                            clip=False)

        fig, ax = plt.subplots()
        ax.contourf(Xi, Yi, Pi,
                    levels=levels,
                    cmap=cmap,
                    norm=norm,
                    extend='both')

        ax.set_xlabel(mass_label("X"))
        ax.set_ylabel(mass_label("S"))

        if self.log_x:
            ax.set_xscale("log")
        if self.log_y:
            ax.set_yscale("log")

        # Legend: manual mapping of color to label
        import matplotlib.patches as mpatches
        patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(num_bins)]
        ax.legend(handles=patches, title="Scan precision", loc="upper right", frameon=True)

        fig.tight_layout()
        fig.savefig(os.path.join(self.output_dir, f"{self.decay}_{self.identifier}_precision_map.png"))

def plot_interpolation(X_mass: np.ndarray,
                       S_mass: np.ndarray,
                       xb: np.ndarray,
                       file_name: str,
                       limit_type: Literal["max", "expected", "observed"],
                       contour_masks: Optional[List[Dict]] = None,
                       log_x: bool = False,
                       log_y: bool = False) -> None:
    """
    Create a filled contour plot with optional exclusion overlays.

    Args:
        X_mass (np.ndarray): 2D array of X mass grid.
        S_mass (np.ndarray): 2D array of S mass grid.
        xb (np.ndarray): 2D array of interpolated xb values.
        file_name (str): Output file path.
        limit_type (Literal["max", "expected", "observed"]): Label for the xb type.
        contour_masks (Optional[List[Dict]]): Optional list of overlay mask definitions.
        log_x (bool): Use log scale for x-axis.
        log_y (bool): Use log scale for y-axis.
    """
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

def plot_xb_to_limit_ratio(xb: np.ndarray,
                           limit: np.ndarray,
                           X: np.ndarray,
                           S: np.ndarray,
                           file_name: str,
                           log_x: bool = False,
                           log_y: bool = False) -> None:
    """
    Plot a categorized xb/limit ratio map with discrete color bands.

    Args:
        xb (np.ndarray): Array of xb values.
        limit (np.ndarray): Array of limit values at each point.
        X (np.ndarray): X mass coordinates.
        S (np.ndarray): S mass coordinates.
        file_name (str): Output file path.
        log_x (bool): Log scale for X axis.
        log_y (bool): Log scale for Y axis.
    """
    ratio = np.divide(xb, limit, out=np.full_like(xb, np.nan), where=(limit > 0))
    Xi, Yi, Zi = interpolate_grid(X, S, ratio)

    # Thresholds: all except INSENSITIVE and MISSING, include SATURATED separately
    thresholds = [p.threshold() for p in Precision if p not in {Precision.MISSING, Precision.INSENSITIVE, Precision.SATURATED}]
    saturated_threshold = Precision.SATURATED.threshold()

    # Build level boundaries
    levels = [0.0] + thresholds + [1.0, saturated_threshold]
    levels.append(saturated_threshold * 1.2)  # pad upper range

    # Labels: one per bin
    labels = [f"< {thresholds[0]:.3f}"]
    labels += [f"{thresholds[i]:.2f}-{thresholds[i+1]:.2f}" for i in range(len(thresholds) - 1)]
    labels.append(f"{thresholds[-1]:.2f}-1.0")
    labels.append(f"1.0-{saturated_threshold:.0f}")
    labels.append(f"> {saturated_threshold:.0f}")

    num_bins = len(levels) - 1
    colors = get_discrete_colors(num_bins,
                                 cmap_name="plasma")

    cmap = mcolors.ListedColormap(colors)
    norm = BoundaryNorm(levels,
                        ncolors=cmap.N,
                        clip=True)

    fig, ax = plt.subplots()
    ax.contourf(Xi, Yi, Zi,
                levels=levels,
                cmap=cmap,
                norm=norm,
                extend='both')

    ax.set_xlabel(mass_label("X"))
    ax.set_ylabel(mass_label("S"))

    if log_x:
        ax.set_xscale("log")
    if log_y:
        ax.set_yscale("log")

    # Construct a manual legend
    patches = [mpatches.Patch(color=colors[i], label=labels[i]) for i in range(len(labels))]
    ax.legend(handles=patches, title="xb / limit", loc="upper right", frameon=True)

    fig.tight_layout()
    fig.savefig(file_name)

def load_data(file_path: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """
    Load XMass, SMass, and MaxXB from a .tsv file using column names.

    Args:
        file_path (str): Path to the .tsv file.

    Returns:
        Tuple of arrays: (X_mass, S_mass, xb_max, precision)

    Raises:
        RuntimeError: If the file cannot be read or parsed correctly.
    """
    try:
        df = pd.read_csv(file_path, sep='\t')
        required_cols = {'XMass', 'SMass', 'xb', 'precision'}
        if not required_cols.issubset(df.columns):
            missing = required_cols - set(df.columns)
            raise ValueError(f"Missing required columns in TSV file: {missing}")
        
        X_mass = df['XMass'].to_numpy()
        S_mass = df['SMass'].to_numpy()
        xbmax = df['xb'].to_numpy() * 1000 # Convert to fb
        precision_raw = df['precision'].astype(str).str.lower()
        precision_enum = np.array([Precision.from_string(p).value for p in precision_raw])
        return X_mass, S_mass, xbmax, precision_enum

    except Exception as e:
        raise RuntimeError(f"Failed to read or parse data from {file_path}: {e}")

def build_contour_mask_sets(interp_masks: Dict[str, np.ndarray],
                            include_sigma: bool = True) -> Tuple[List[Dict[str, object]], List[Dict[str, object]]]:
    """
    Build contour mask sets for plotting observed and expected limit overlays.

    Args:
        interp_masks (Dict[str, np.ndarray]): Dictionary of interpolated binary mask arrays.
        include_sigma (bool): Include ±1σ and ±2σ bands if True.

    Returns:
        Tuple of:
            - Observed mask definitions
            - Expected mask definitions (possibly trimmed)
    """
    observed_masks = [
        {
            "mask": interp_masks["observed"],
            "label": "TRSM",
            "style": {"color": "red", "linestyle": "-"}
        }
    ]

    expected_masks = [
        {
            "mask": interp_masks["expected_m2"],
            "label": r"$-2\sigma$",
            "style": {"color": "purple", "linestyle": ":"}
        },
        {
            "mask": interp_masks["expected_m1"],
            "label": r"$-1\sigma$",
            "style": {"color": "purple", "linestyle": "-."}
        },
        {
            "mask": interp_masks["expected"],
            "label": "Median",
            "style": {"color": "red", "linestyle": "-"}
        },
        {
            "mask": interp_masks["expected_p1"],
            "label": r"$+1\sigma$",
            "style": {"color": "orange", "linestyle": "-."}
        },
        {
            "mask": interp_masks["expected_p2"],
            "label": r"$+2\sigma$",
            "style": {"color": "orange", "linestyle": ":"}
        }
    ]

    if not include_sigma:
        expected_masks = [expected_masks[2]]  # Only the median

    return observed_masks, expected_masks
