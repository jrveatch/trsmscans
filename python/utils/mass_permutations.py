
import json
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
    """

    permutations_file = os.path.join(data_dir(),"mass_points",f"{decay}_{identifier}.json")

    permutations: List[Tuple[int, int, bool]] = []

    # Read permutations
    try:
        with open(permutations_file, 'r') as perm_file:
            data = json.load(perm_file)
            for mass_point in data["mass_points"]:
                permutations.append((mass_point["mX"], mass_point["mS"], mass_point["resolvable"]))
    except Exception as e:
        print(f"Error reading permutations file {permutations_file}: {e}")
        raise

    return permutations
