
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
        units = self.data.get("units")
        if units is None:
            raise KeyError("Missing required key: 'units'")
        if not isinstance(units, str):
            raise TypeError(f"'units' must be a string, got {type(units).__name__}")
        return 1000.0 if units == "pb" else 1.0

    @cached_property
    def includes_decay(self) -> bool:
        val = self.data.get("includes_decay")
        if val is None:
            raise KeyError("Missing required key: 'includes_decay'")
        if not isinstance(val, bool):
            raise TypeError(f"'includes_decay' must be a bool, got {type(val).__name__}")
        return val

    def _gather_mass_point_data(self) -> List[Dict[str, Any]]:
        scale = self.xsec_conversion
        return [
            {
                "mX": p.get("mX"),
                "mS": p.get("mS"),
                "resolvable": p.get("resolvable", True),
                "limits": {
                    "observed": p.get("observed_limit", -1.0) * scale,
                    "expected": p.get("expected_limit", -1.0) * scale,
                    "expected_m1": p.get("expected_limit_m1", -1.0) * scale,
                    "expected_p1": p.get("expected_limit_p1", -1.0) * scale,
                    "expected_m2": p.get("expected_limit_m2", -1.0) * scale,
                    "expected_p2": p.get("expected_limit_p2", -1.0) * scale,
                },
            }
            for p in self.data.get("mass_points", [])
        ]

    def get_mass_permutations(self) -> List[Tuple[int, int, bool, Dict[str,float]]]:
        """
        Gets a list of mass permutations for a the mass list.

        Returns:
            List[Tuple[int, int, bool, Dict[str, float]]]:
                A list of tuples containing mass points, resolvable status, and dictionary of limits.
        """
        return [
            (d["mX"], d["mS"], d["resolvable"], d["limits"])
            for d in self._gather_mass_point_data()
        ]

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
        data = self._gather_mass_point_data()
        return LimitData(
            X_mass=np.array([d["mX"] for d in data]),
            S_mass=np.array([d["mS"] for d in data]),
            observed=np.array([d["limits"]["observed"] for d in data]),
            expected=np.array([d["limits"]["expected"] for d in data]),
            expected_m1=np.array([d["limits"]["expected_m1"] for d in data]),
            expected_p1=np.array([d["limits"]["expected_p1"] for d in data]),
            expected_m2=np.array([d["limits"]["expected_m2"] for d in data]),
            expected_p2=np.array([d["limits"]["expected_p2"] for d in data]),
        )
