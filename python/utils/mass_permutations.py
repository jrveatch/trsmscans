#!/usr/bin/env python3

import csv
import os

def get_mass_permutations(decay: str,
                          identifier: str) -> None:
    """
    Returns a list of mass permutations for a given decay mode and identifier.

    Args:
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.
    """

    permutations_file = os.environ['DATADIR']+f"mass_points/{decay}_{identifier}.txt"

    permutations = []

    # Read permutations
    try:
        with open(permutations_file, 'r') as perm_file:
            reader = csv.reader(perm_file, delimiter=" ")
            for i, line in enumerate(reader):
                # Skip the first line (headers) and filter out commented lines
                if i == 0 or line[0].startswith("#"):
                    continue
                permutations.append((line[0], line[1], line[2].lower() == "true"))
    except Exception as e:
        print(f"Error reading permutations file {permutations_file}: {e}")
        return

    return permutations
