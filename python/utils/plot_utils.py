
import numpy as np
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
