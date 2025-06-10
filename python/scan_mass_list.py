#!/usr/bin/env python3

import argparse
import subprocess

from utils.decay_utils import get_non_resolvable_decay
from utils.mass_permutations import get_mass_permutations

def scan_mass_list(model: str,
                   decay: str,
                   identifier: str,
                   batch_mode: bool) -> None:
    """
    Scan a list of mass points based on permutations of two values.
    By default, it runs locally, but can be used for HTCondor submission.

    Args:
        model (str): Name of the theoretical model.
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.
        batch_mode (bool): Whether to submit jobs using HTCondor.
    """

    permutations = get_mass_permutations(decay=decay, identifier=identifier)

    command = "scan_htcondor.py" if batch_mode else "scan.py"

    job_count = 0

    for XMass, SMass, resolvable in permutations:
        decay_mode = decay
        # If mass point isn't resolvable, use the non-resolvable decay
        if not resolvable:
            decay_mode = get_non_resolvable_decay(decay)

        arg_list = [
            "-m", model,
            "-d", decay_mode,
            "-X", str(XMass),
            "-S", str(SMass),
            "-s", "zoom",
            "-n", "10000"
        ]
        subprocess.run([command, *arg_list], text=True)
        job_count += 1

    print(f"Submitted {job_count} jobs.")

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    arg_parser.add_argument("-b", "--batch", action="store_true", help="Use batch mode for HTCondor submission")
    args = arg_parser.parse_args()

    scan_mass_list(model=args.model,
                   decay=args.decay,
                   identifier=args.identifier,
                   batch_mode=args.batch)
