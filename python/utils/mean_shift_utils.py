
import logging
import numpy as np
from typing import Dict

from utils.param_space import ParamSpace
from utils.point import Point

# get logger
logger = logging.getLogger(__name__)

def mean_shift(arrays: Dict[str,np.ndarray],
               Z: np.ndarray,
               param_space: ParamSpace,
               z_exp: float = 1.0) -> None:
    """
    Updates the center value based on weighted sample pairs of X_i and Z.

    Args:
        arrays (Dict[str, np.ndarray]): Dictionary where keys are parameter names, 
                                        and values are NumPy arrays representing dimensions.
        Z (np.ndarray): Function values for the sample space.
        param_space (ParamSpace): Object with a `reposition_center` method to update the center.
        z_exp (float): Exponent applied to Z before normalization.

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

    # Store parameter names
    param_names = list(arrays.keys())

    # Convert arrays to NumPy array
    XX = np.array([arrays[name] for name in param_names], dtype=np.float64)

    # Apply exponent and normalize Z
    Z_mod = np.power(Z, z_exp)
    Z_sum = np.sum(Z_mod)
    Z_safe_sum = np.maximum(Z_sum, np.finfo(Z.dtype).eps)
    nZ = Z_mod / Z_safe_sum

    # Verbose logging
    logger.verbose("\nPre-shift:\n==========")
    logger.verbose(f"Parameter names: {list(arrays.keys())}")
    for i, X in enumerate(XX):
        logger.verbose(f"X_{i}:{X}")
    logger.verbose(f"nZ: {nZ}")

    # Compute weighted mean shift
    means = np.einsum('ij,j->i', XX, nZ)

    # Create shifted point
    shifted_point = Point(model=param_space.model, par_vals={name: value for name, value in zip(param_names, means)})

    # Update center position
    param_space.reposition_center(shifted_point)