#!/usr/bin/env python3

import os
from functools import lru_cache
from typing import List, Set
import yaml

# local modules
from utils.env_utils import data_dir

class DecayConfigManager:
    def __init__(self):
        file_name = os.path.join(data_dir(), "decay_modes.yml")

        # Load the configuration file once during initialization
        with open(file_name, 'r') as config_file:
            config = yaml.safe_load(config_file)
        
        self.allowed_decay_modes = config.get("allowed_decay_modes", {})
        # Create a reverse mapping from values to groups and their non-resolvable version
        self.decay_to_group = {}
        self.non_resolvable_map = {}
        self.valid_decay_modes: List[str] = []

        for group, details in self.allowed_decay_modes.items():
            self.valid_decay_modes.extend(details["all_modes"])
            for mode in details["all_modes"]:
                self.decay_to_group[mode] = group
            self.non_resolvable_map[group] = details.get("non_resolvable")

    def is_decay_allowed(self, decay):
        """
        Check whether a given decay is allowed in any decay group.
        """
        return decay in self.valid_decay_modes

    def get_non_resolvable_decay(self, decay):
        """
        Get the non-resolvable version of the decay group to which the given decay belongs.
        """
        group = self.decay_to_group.get(decay)
        if not group:
            raise ValueError(f"Decay '{decay}' not found in any decay group.")
        
        # Return the non-resolvable version for the decay group
        return self.non_resolvable_map.get(group)

@lru_cache(maxsize=None)
def valid_decays() -> Set[str]:

    decay_config_manager = DecayConfigManager()

    return decay_config_manager.valid_decay_modes

def is_valid_decay(decay_mode: str) -> bool:

    decay_config_manager = DecayConfigManager()

    return decay_config_manager.is_decay_allowed(decay_mode)

def get_non_resolvable_decay(decay: str) -> str:

    decay_config_manager = DecayConfigManager()

    return decay_config_manager.get_non_resolvable_decay(decay)
