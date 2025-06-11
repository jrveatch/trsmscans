
import json
import numpy as np
import os
from typing import List, Tuple

# local modules
from utils.env_utils import data_dir

def get_mass_permutations(decay: str,
                          identifier: str) -> List[Tuple[int, int, bool]]:
    """
    Returns a list of mass permutations for a given decay mode and identifier.

    Args:
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.

    Returns:
        List[Tuple[int, int, bool]]: A list of tuples containing mass points and resolvable status.
    """

    permutations_file = os.path.join(data_dir(),"mass_points",f"{decay}_{identifier}.json")

    # Read permutations
    try:
        with open(permutations_file, 'r') as perm_file:
            data = json.load(perm_file)
            permutations = [
                (p["mX"], p["mS"], p["resolvable"]) 
                for p in data["mass_points"]
            ]
        return permutations
    except Exception as e:
        print(f"Error reading permutations file {permutations_file}: {e}")
        raise

def load_limit_data(limit_type: str,
                    decay: str,
                    identifier: str) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """
    Loads expected or observed limits from a JSON file.

    Args:
        limit_type (str): 'expected' or 'observed'
        decay (str): Decay mode
        identifier (str): Identifier for this run

    Returns:
        Tuple[np.ndarray, np.ndarray, np.ndarray]: Arrays of mX, mS, and limit values

    Raises:
        ValueError: If limit_type is not recognized or required fields are missing
        RuntimeError: On file access or parsing errors
    """
    if limit_type not in ("expected", "observed"):
        raise ValueError("limit_type must be 'expected' or 'observed'")

    limit_file = os.path.join(data_dir(), "limits", f"{decay}_{identifier}_limits.json")

    try:
        with open(limit_file, "r") as f:
            data = json.load(f)

        x_vals, y_vals, z_vals = [], [], []
        for point in data["mass_points"]:
            if limit_type + "_limit" not in point:
                raise ValueError(f"Missing {limit_type}_limit in mass point entry")
            x_vals.append(point["mX"])
            y_vals.append(point["mS"])
            z_vals.append(point[f"{limit_type}_limit"])

        return np.array(x_vals), np.array(y_vals), np.array(z_vals)

    except Exception as e:
        raise RuntimeError(f"Failed to load {limit_type} limits from {limit_file}: {e}")
