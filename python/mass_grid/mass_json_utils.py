
import json
import numpy as np
import os
from typing import Dict, List, NamedTuple, Tuple

# local modules
from utils.env_utils import data_dir

def get_mass_permutations(decay: str,
                          identifier: str) -> List[Tuple[int, int, bool, Dict[str,float]]]:
    """
    Returns a list of mass permutations for a given decay mode and identifier.

    Args:
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.

    Returns:
        List[Tuple[int, int, bool, Dict[str, float]]]:
            A list of tuples containing mass points, resolvable status, and dictionary of limits.
    """

    permutations_file = os.path.join(data_dir(),"mass_points",f"{decay}_{identifier}.json")

    # Read permutations
    try:
        with open(permutations_file, 'r') as perm_file:
            data = json.load(perm_file)
            permutations = [
                (p["mX"], p["mS"], p["resolvable"],
                 {"observed": p["observed_limit"], # TODO: Handle case where limits are missing
                  "expected": p["expected_limit"],
                  "expected_m1": p["expected_limit_m1"],
                  "expected_p1": p["expected_limit_p1"],
                  "expected_m2": p["expected_limit_m2"],
                  "expected_p2": p["expected_limit_p2"]}) 
                for p in data["mass_points"]
            ]
        return permutations
    except Exception as e:
        print(f"Error reading permutations file {permutations_file}: {e}")
        raise

class LimitData(NamedTuple):
    X_mass: np.ndarray
    S_mass: np.ndarray
    observed: np.ndarray
    expected: np.ndarray
    expected_m1: np.ndarray
    expected_p1: np.ndarray
    expected_m2: np.ndarray
    expected_p2: np.ndarray

def load_limit_data(decay: str,
                    identifier: str) -> LimitData:
    """
    Loads mass point limit data from a JSON file for a given decay mode and identifier.

    This includes the observed limit, expected limit, and ±1σ/±2σ expected variations
    for each (mX, mS) mass point.

    Args:
        decay (str): The decay mode (e.g., "SHbbbb").
        identifier (str): The identifier for the dataset (e.g., "CMS_boosted").

    Returns:
        LimitData: A named tuple containing:
            - X_mass (np.ndarray): X mass values.
            - S_mass (np.ndarray): S mass values.
            - observed (np.ndarray): Observed limits.
            - expected (np.ndarray): Expected median limits.
            - expected_m1 (np.ndarray): Expected -1σ limits.
            - expected_p1 (np.ndarray): Expected +1σ limits.
            - expected_m2 (np.ndarray): Expected -2σ limits.
            - expected_p2 (np.ndarray): Expected +2σ limits.

    Raises:
        RuntimeError: If the JSON file is missing, malformed, or contains unexpected data.
    """

    limit_file = os.path.join(data_dir(), "mass_points", f"{decay}_{identifier}.json")

    try:
        with open(limit_file, "r") as f:
            data = json.load(f)

        X_mass_vals, S_mass_vals, obs_limit_vals, exp_limit_vals = [], [], [], []
        exp_m1_limit_vals, exp_p1_limit_vals, exp_m2_limit_vals, exp_p2_limit_vals = [], [], [], []
        for point in data["mass_points"]:
            X_mass_vals.append(point["mX"])
            S_mass_vals.append(point["mS"])
            obs_limit_vals.append(point["observed_limit"])
            exp_limit_vals.append(point["expected_limit"])
            exp_m1_limit_vals.append(point["expected_limit_m1"])
            exp_p1_limit_vals.append(point["expected_limit_p1"])
            exp_m2_limit_vals.append(point["expected_limit_m2"])
            exp_p2_limit_vals.append(point["expected_limit_p2"])

        return LimitData(
            X_mass=np.array(X_mass_vals),
            S_mass=np.array(S_mass_vals),
            observed=np.array(obs_limit_vals),
            expected=np.array(exp_limit_vals),
            expected_m1=np.array(exp_m1_limit_vals),
            expected_p1=np.array(exp_p1_limit_vals),
            expected_m2=np.array(exp_m2_limit_vals),
            expected_p2=np.array(exp_p2_limit_vals)
        )

    except Exception as e:
        raise RuntimeError(f"Failed to load limits from {limit_file}: {e}")
