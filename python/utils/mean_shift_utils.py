
import numpy as np
from typing import Dict

from utils.config_loader import ConfigLoader
from utils.param_space import ParamSpace
from utils.point import Point

# get logger
from utils.logging_utils import VERBOSE_LEVEL
import logging
logger = logging.getLogger(__name__)

def mean_shift(arrays: Dict[str,np.ndarray],
               Z: np.ndarray,
               param_space: ParamSpace,
               config_loader: ConfigLoader) -> None:
    """
    Updates the center value based on weighted sample pairs of X_i and Z.

    Args:
        arrays (Dict[str, np.ndarray]): Dictionary where keys are parameter names,
                                        and values are NumPy arrays representing dimensions.
        Z (np.ndarray): Function values for the sample space.
        param_space (ParamSpace): Object with a `reposition_center` method to update the center.
        z_exp (float): Exponent applied to Z before normalization.
        use_adaptive_z_exp (bool): Flag to enable adaptive modifications to z_exp based on the terrain.

    Raises:
        ValueError: If the lengths of parameter arrays do not match the length of Z.
    """

    # Make sure all inputs are the same length
    num_samples = len(Z)
    for key, val in arrays.items():
        if len(val) != num_samples:
            raise ValueError(
                f"Length mismatch for parameter '{key}': expected {num_samples} samples (from Z), "
                f"but got {len(val)}."
            )

    # Get mean shift configuration from config file
    try:
        z_exp: float = config_loader.get('meanshift', 'z_exp')
        use_adaptive_z_exp: bool = config_loader.get('meanshift', 'use_adaptive_z_exp')
        z_exp_alpha: float = config_loader.get('meanshift', 'z_exp_alpha')
    except Exception as e:
        logger.exception(e)
        raise

    # Store parameter names
    param_names = list(arrays.keys())

    # Convert arrays to NumPy array
    XX = np.array([arrays[name] for name in param_names], dtype=np.float64)

    # Adapt z_exp using coefficients of variation
    if use_adaptive_z_exp:
        z_exp = compute_adaptive_z_exp(Z=Z,
                                       alpha=z_exp_alpha)

    # Apply exponent and normalize Z
    Z_mod = np.power(Z, z_exp)
    Z_sum = np.sum(Z_mod)
    Z_safe_sum = np.maximum(Z_sum, np.finfo(Z.dtype).eps)
    nZ = Z_mod / Z_safe_sum

    # Verbose logging
    if logger.isEnabledFor(VERBOSE_LEVEL):
        logger.verbose("\nPre-shift:\n==========")  # type: ignore[attr-defined]
        logger.verbose(f"Parameter names: {list(arrays.keys())}")  # type: ignore[attr-defined]
        for i, X in enumerate(XX):
            logger.verbose(f"X_{i}:{X}")  # type: ignore[attr-defined]
        logger.verbose(f"nZ: {nZ}")  # type: ignore[attr-defined]

    # Compute weighted mean shift
    means = np.einsum('ij,j->i', XX, nZ)

    # Create shifted point
    shifted_point = Point(model=param_space.model, par_vals=dict(zip(param_names, means)))

    # Update center position
    param_space.reposition_center(shifted_point)

def compute_adaptive_z_exp(Z: np.ndarray,
                           alpha: float = 1.0,
                           min_exp: float = 0.9,
                           max_exp: float = 3.0) -> float:
    """Compute adaptive z_exp from coefficient of variation of Z."""
    mean_Z = np.mean(Z)
    std_Z = np.std(Z)
    cv = std_Z / np.maximum(mean_Z, np.finfo(Z.dtype).eps)
    z_exp = 1 + alpha * (cv - 1)
    return np.clip(z_exp, min_exp, max_exp)
