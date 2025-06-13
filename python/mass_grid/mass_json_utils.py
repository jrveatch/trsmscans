
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

def load_limit_data(decay: str,
                    identifier: str) -> Tuple[np.ndarray, ...]:
    """
    Loads expected or observed limits from a JSON file.

    Args:
        decay (str): Decay mode
        identifier (str): Identifier for this run

    Returns:
        Tuple[np.ndarray, ...]: Arrays of mX, mS, and limit values

    Raises:
        ValueError: If required fields are missing
        RuntimeError: On file access or parsing errors
    """

    limit_file = os.path.join(data_dir(), "mass_points", f"{decay}_{identifier}.json")

    try:
        with open(limit_file, "r") as f:
            data = json.load(f)

        X_mass_vals, S_mass_vals, obs_limit_vals, exp_limit_vals = [], [], [], []
        for point in data["mass_points"]:
            X_mass_vals.append(point["mX"])
            S_mass_vals.append(point["mS"])
            obs_limit_vals.append(point["observed_limit"])
            exp_limit_vals.append(point["expected_limit"])

        return (np.array(X_mass_vals), np.array(S_mass_vals), np.array(obs_limit_vals), np.array(exp_limit_vals))

    except Exception as e:
        raise RuntimeError(f"Failed to load limits from {limit_file}: {e}")
