
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from typing import Tuple

def xb_label(limit_type: str) -> str:
    """
    Returns the label for the interpolated plot based on the type of limit.

    Args:
        limit_type (str): The type of limit. Must be one of "max", "expected", or "observed".

    Returns:
        str: A LaTeX-formatted label for the interpolated plot.

    Raises:
        ValueError: If the limit_type is not recognized.
    """
    if limit_type == "max":
        prefix = "Max allowed"
    elif limit_type == "expected":
        prefix = "Expected limit on"
    elif limit_type == "observed":
        prefix = "Observed limit on"
    else:
        raise ValueError(f"Unrecognized limit_type: {limit_type}")
    
    return fr"{prefix} $\sigma\times BR$ [fb]"

def mass_label(particle: str) -> str:
    """
    Returns the label for the mass plot.
    
    Returns:
        str: The label for the mass plot.
    """
    return fr"$m_{{{particle}}}$ [GeV]"

def interpolate_grid(x: np.ndarray,
                     y: np.ndarray,
                     z: np.ndarray, 
                     resolution: Tuple[int, int]=(200, 200),
                     method: str = 'linear'
                    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Create interpolated 2D grid from scattered data points.

    Args:
        x (np.ndarray): 1D array of x-coordinates.
        y (np.ndarray): 1D array of y-coordinates.
        z (np.ndarray): 1D array of values at the (x, y) coordinates.
        resolution (tuple[int, int]): Resolution of the output grid.
        method (str): Interpolation method passed to `scipy.interpolate.griddata`.
                      Must be one of:
                        - 'linear': Triangulates input data and performs linear interpolation.
                        - 'nearest': Uses nearest-neighbor interpolation.
                        - 'cubic': Performs cubic interpolation on a regular grid (only works in 2D).

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Meshgrid arrays (Xi, Yi) and interpolated values (Zi).
    """
    xi = np.linspace(x.min(), x.max(), resolution[0])
    yi = np.linspace(y.min(), y.max(), resolution[1])
    Xi, Yi = np.meshgrid(xi, yi)
    Zi = griddata((x, y), z, (Xi, Yi), method=method)
    return Xi, Yi, Zi

def get_discrete_colors(n: int,
                        cmap_name: str = "viridis") -> list:
    """
    Return n discrete colors sampled from a matplotlib colormap.
    """
    cmap = plt.get_cmap(cmap_name)
    return [cmap(i) for i in np.linspace(0, 1, n)]

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
