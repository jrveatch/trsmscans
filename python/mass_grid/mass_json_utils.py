
from functools import cached_property
import json
import numpy as np
import os
from typing import Any, Dict, List, NamedTuple, Tuple

# local modules
from utils.env_utils import data_dir

class LimitData(NamedTuple):
    X_mass: np.ndarray
    S_mass: np.ndarray
    observed: np.ndarray
    expected: np.ndarray
    expected_m1: np.ndarray
    expected_p1: np.ndarray
    expected_m2: np.ndarray
    expected_p2: np.ndarray

class MassList:

    def __init__(self,
                 decay: str,
                 identifier: str):
        """
        Loads mass list information from JSON file.

        Args:
            decay (str): The decay mode (e.g., "SHbbbb").
            identifier (str): The identifier for the dataset (e.g., "CMS").

        Raises:
            RuntimeError: If the JSON file is missing, malformed, or contains unexpected data.
        """
        file_name = os.path.join(data_dir(), "mass_points", f"{decay}_{identifier}.json")
        try:
            with open(file_name, 'r') as file:
                self.__data = json.load(file)
        except Exception as e:
            raise RuntimeError(f"Error reading mass list file {file_name}: {e}")

    @property
    def data(self) -> Dict[str,Any]:
        return self.__data

    @cached_property
    def xsec_conversion(self) -> float:
        units: str = self.data.get("units")
        if units == "pb":
            return 1000.0
        return 1.0

    @cached_property
    def includes_decay(self) -> bool:
        return self.data.get("includes_decay")

    def get_mass_permutations(self) -> List[Tuple[int, int, bool, Dict[str,float]]]:
        """
        Gets a list of mass permutations for a the mass list.

        Returns:
            List[Tuple[int, int, bool, Dict[str, float]]]:
                A list of tuples containing mass points, resolvable status, and dictionary of limits.
        """

        scale = self.xsec_conversion

        permutations = [
            (
                p.get("mX"), p.get("mS"), p.get("resolvable"),
                {
                "observed": p.get("observed_limit", -1.0) * scale,
                "expected": p.get("expected_limit", -1.0) * scale,
                "expected_m1": p.get("expected_limit_m1", -1.0) * scale,
                "expected_p1": p.get("expected_limit_p1", -1.0) * scale,
                "expected_m2": p.get("expected_limit_m2", -1.0) * scale,
                "expected_p2": p.get("expected_limit_p2", -1.0) * scale
                }
            ) 
            for p in self.data["mass_points"]
        ]
        return permutations

    def load_limit_data(self) -> LimitData:
        """
        Gets limit data for the mass list.

        This includes the observed limit, expected limit, and ±1σ/±2σ expected variations
        for each (mX, mS) mass point.

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
        """

        scale = self.xsec_conversion

        X_mass_vals, S_mass_vals, obs_limit_vals, exp_limit_vals = [], [], [], []
        exp_m1_limit_vals, exp_p1_limit_vals, exp_m2_limit_vals, exp_p2_limit_vals = [], [], [], []
        for point in self.data["mass_points"]:
            X_mass_vals.append(point.get("mX"))
            S_mass_vals.append(point.get("mS"))
            obs_limit_vals.append(point.get("observed_limit",-1.0) * scale)
            exp_limit_vals.append(point.get("expected_limit",-1.0) * scale)
            exp_m1_limit_vals.append(point.get("expected_limit_m1",-1.0) * scale)
            exp_p1_limit_vals.append(point.get("expected_limit_p1",-1.0) * scale)
            exp_m2_limit_vals.append(point.get("expected_limit_m2",-1.0) * scale)
            exp_p2_limit_vals.append(point.get("expected_limit_p2",-1.0) * scale)

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
