
from functools import cached_property
import json
import numpy as np
import os
from typing import Any, Dict, List, NamedTuple, Tuple

# local modules
from utils.env_utils import data_dir

class LimitData(NamedTuple):   
    """
    Container for limit data across mass points.
    """
    X_mass: np.ndarray
    S_mass: np.ndarray
    observed: np.ndarray
    expected: np.ndarray
    expected_m1: np.ndarray
    expected_p1: np.ndarray
    expected_m2: np.ndarray
    expected_p2: np.ndarray

class MassList:
    """
    Handles loading and interpreting mass point data from JSON files,
    including cross-section conversions and limit retrieval.
    """
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
    def data(self) -> Dict[str, Any]:
        """
        Returns the raw JSON-decoded data dictionary.

        Returns:
            Dictionary containing the full content of the mass list JSON.
        """
        return self.__data

    @cached_property
    def units(self) -> str:
        """
        Returns the cross-section units.

        Raises:
            KeyError: If 'units' key is missing.
            TypeError: If 'units' is not a string.
        """
        _units = self.data.get("units")
        if _units is None:
            raise KeyError("Missing required key: 'units'")
        if not isinstance(_units, str):
            raise TypeError(f"'units' must be a string, got {type(_units).__name__}")
        return _units

    @cached_property
    def xsec_conversion(self) -> float:
        """
        Returns the cross-section unit conversion factor.

        Returns:
            1000.0 if units are "pb", else 1.0 (assumes default units are fb).
        """
        return 1000.0 if self.units == "pb" else 1.0

    @cached_property
    def includes_decay(self) -> bool:
        """
        Indicates whether decay branching ratios are already included in the limits.

        Returns:
            True if limits include decay; False otherwise.

        Raises:
            KeyError: If 'includes_decay' key is missing.
            TypeError: If 'includes_decay' is not a bool.
        """
        val = self.data.get("includes_decay")
        if val is None:
            raise KeyError("Missing required key: 'includes_decay'")
        if not isinstance(val, bool):
            raise TypeError(f"'includes_decay' must be a bool, got {type(val).__name__}")
        return val

    def _gather_mass_point_data(self) -> List[Dict[str, Any]]:
        """
        Internal helper to extract and rescale mass point data.

        Returns:
            A list of dictionaries, one per mass point, with fields:
            mX, mS, resolvable, and scaled limit values.
        """
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

    def get_mass_permutations(self) -> List[Tuple[int, int, bool, Dict[str, float]]]:
        """
        Retrieves all mass permutations in the dataset.

        Each entry includes (mX, mS, resolvable, limits).

        Returns:
            A list of tuples:
                - mX (int): Mass of the X particle.
                - mS (int): Mass of the S particle.
                - resolvable (bool): Whether the mass point is resolvable.
                - limits (Dict[str, float]): Scaled observed and expected limits.
        """
        return [
            (d["mX"], d["mS"], d["resolvable"], d["limits"])
            for d in self._gather_mass_point_data()
        ]

    def load_limit_data(self) -> LimitData:
        """
        Loads and formats the limit data as arrays suitable for plotting or analysis.

        Returns:
            LimitData: Named tuple containing arrays of mass points and limits.
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
