#!/usr/bin/env python3

import argparse
import subprocess

from utils.mass_json_utils import get_mass_permutations

def scan_mass_list(model: str,
                   decay: str,
                   identifier: str) -> None:
    """
    Processes directories based on permutations of two values, includes headers, and writes the last line of .tsv files to a new .tsv file.

    Args:
        model (str): Name of the theoretical model.
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.
    """

    permutations = get_mass_permutations(decay=decay, identifier=identifier)

    for XMass, SMass, _ in permutations:
        arg_list = [
            "-m", model,
            "-X", str(XMass),
            "-S", str(SMass),
            "-n", "10000"
        ]
        subprocess.run(["prescan.py", *arg_list], text=True)

        # TODO: Add htcondor submission if needed

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    args = arg_parser.parse_args()

    scan_mass_list(model=args.model,
                   decay=args.decay,
                   identifier=args.identifier)
