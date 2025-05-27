#!/usr/bin/env python3

"""
Manages allowed decay modes and their groupings for model analysis.

Loads a YAML configuration defining valid decay modes and provides
functions to check for validity, retrieve grouped metadata, and resolve
non-distinct decay variants.
"""

import os
from functools import lru_cache
from typing import Dict, List, TypedDict
import yaml

# local modules
from utils.env_utils import data_dir

class DecayGroup(TypedDict):
    all_modes: List[str]
    non_resolvable: str

class DecayConfigManager:
    """
    Loads and manages allowed decay modes and their group relationships.

    The configuration is loaded from 'decay_modes.yml' located in the data directory.
    Each decay group includes a list of all decay modes and a representative
    "non-resolvable" version (used for merging or comparison).

    Attributes:
        allowed_decay_modes (Dict[str, DecayGroup]): Mapping from group name to decay modes.
        decay_to_group (Dict[str, str]): Maps each decay mode to its group name.
        non_resolvable_map (Dict[str, str]): Maps group name to its non-resolvable decay mode.
        valid_decay_modes (List[str]): Flat list of all allowed decay modes.

    Methods:
        is_decay_allowed(decay: str) -> bool:
            Checks if a decay mode is among the allowed modes.

        get_non_resolvable_decay(decay: str) -> str:
            Returns the non-resolvable representative for a given decay mode.
    """

    def __init__(self):
        file_name = os.path.join(data_dir(), "decay_modes.yml")

        # Load the configuration file once during initialization
        with open(file_name, 'r') as config_file:
            config = yaml.safe_load(config_file)

        self.allowed_decay_modes: Dict[str, DecayGroup] = config.get("allowed_decay_modes", {})
        # Create a reverse mapping from values to groups and their non-resolvable version
        self.decay_to_group: Dict[str, str] = {}
        self.non_resolvable_map: Dict[str, str] = {}
        self.valid_decay_modes: List[str] = []

        for group, details in self.allowed_decay_modes.items():
            self.valid_decay_modes.extend(details.get("all_modes"))
            for mode in details["all_modes"]:
                self.decay_to_group[mode] = group
            self.non_resolvable_map[group] = details.get("non_resolvable")

    def is_decay_allowed(self,
                         decay: str) -> bool:
        """
        Check whether a given decay is allowed in any decay group.

        Args:
            decay (str): The decay mode to check.

        Returns:
            bool: True if the decay mode is allowed, False otherwise.
        """
        return decay in self.valid_decay_modes

    def get_non_resolvable_decay(self,
                                 decay: str) -> str:
        """
        Returns the non-resolvable representative for the decay group of a given decay mode.

        Decay modes are grouped in the configuration file, where each group has a single
        "non-resolvable" version that should be used in contexts where finer distinctions
        between decay channels are not meaningful (e.g., merging equivalent final states).

        Args:
            decay (str): The decay mode to resolve.

        Returns:
            str: The canonical non-resolvable decay mode for the group.

        Raises:
            ValueError: If the decay mode is not found in any configured group.
        """

        group = self.decay_to_group.get(decay)
        if not group:
            raise ValueError(f"Decay '{decay}' not found in any decay group.")

        # Return the non-resolvable version for the decay group
        return self.non_resolvable_map[group]

@lru_cache(maxsize=None)
def valid_decays() -> List[str]:
    """
    Returns the list of all valid decay modes across all defined decay groups.

    This function caches the result for performance and avoids reloading the YAML file.

    Returns:
        List[str]: All valid decay modes.
    """
    decay_config_manager = DecayConfigManager()
    return decay_config_manager.valid_decay_modes

def is_valid_decay(decay_mode: str) -> bool:
    """
    Check if a decay mode is valid.

    Args:
        decay_mode (str): The decay mode to check.

    Returns:
        bool: True if the decay mode is valid, False otherwise.
    """
    decay_config_manager = DecayConfigManager()
    return decay_config_manager.is_decay_allowed(decay_mode)

def get_non_resolvable_decay(decay: str) -> str:
    """
    Gets the non-resolvable representative decay mode for a given specific mode.

    Args:
        decay (str): A valid decay mode.

    Returns:
        str: The non-resolvable version of the decay mode's group.

    Raises:
        ValueError: If the decay is not part of any configured group.
    """
    decay_config_manager = DecayConfigManager()
    return decay_config_manager.get_non_resolvable_decay(decay)
