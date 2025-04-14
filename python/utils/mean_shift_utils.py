
import logging
import numpy as np
from typing import Dict

from utils.param_space import ParamSpace

# get logger
logger = logging.getLogger(__name__)

def mean_shift(arrays: Dict[str,np.ndarray],
               Z: np.ndarray,
               param_space: ParamSpace) -> None:
    """Updates center value based on sample pairs of X_i and Z.

    Args:
        arrays (Dict[str, np.ndarray]): Dictionary where keys are parameter names, 
                                        and values are NumPy arrays representing dimensions.
        Z (np.ndarray): Function values for the sample space.
        param_space (ParamSpace): Object with a `reposition_center` method to update the center.
    """

    XX = np.array(list(arrays.values()), dtype=np.float64)

    # Normalize Z into a probability distribution (sum=1)
    Z_sum = np.sum(Z)
    nZ = Z / Z_sum if Z_sum != 0 else np.full_like(Z, 1.0 / len(Z))

    # Verbose logging
    logger.verbose("\nPre-shift:\n==========")
    logger.verbose(f"Parameter names: {list(arrays.keys())}")
    for i, X in enumerate(XX):
        logger.verbose(f"X_{i}:{X}")
    logger.verbose(f"nZ: {nZ}")

    # Compute weighted mean shift
    means = np.einsum('ij,j->i', XX, nZ)

    # Update center position
    param_space.reposition_center(tuple(means))