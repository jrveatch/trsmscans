
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
