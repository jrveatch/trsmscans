#!/usr/bin/env python3

import os
import argparse
import json
from typing import Tuple, Optional, Union

from utils.tsv_utils import count_tsv_points
from mass_grid.mass_json_utils import get_mass_permutations
from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir
from utils.model import Model, supported_models
from utils.precision_utils import Precision

def check_mass_list(model_name: str,
                    decay: str,
                    identifier: str,
                    threshold: int,
                    mode: str,
                    strategy: Optional[str] = None,
                    precision: Optional[Precision] = None) -> None:
    """
    Evaluate the scan or prescan completion status for all mass points in a grid.

    For each (X, S) mass point defined by the grid identifier and decay mode,
    this function checks whether:
        - The point is calculable
        - The expected scan or prescan output file exists
        - The number of sampled points meets the threshold

    Each point is categorized into one of:
        - "ok": file exists and contains at least `threshold` points
        - "below_threshold": file exists but contains fewer than `threshold` points
        - "missing": expected file does not exist
        - "non_calculable": the model cannot evaluate this mass point
        - "error": exception occurred while accessing or reading the file

    Results are printed to the screen and written to a summary file:
        <output_dir>/mass_list_counts.txt

    Args:
        model_name (str): The name of the scalar model (e.g., "TRSMBroken").
        decay (str): The decay mode to check (used as-is, no substitutions).
        identifier (str): Grid identifier (used to load the mass grid).
        threshold (int): Minimum number of points required to be considered "ok".
        mode (str): Either "prescan" or "scan", determining file type and location.
        strategy (Optional[str]): Required for scan mode (e.g., "zoom", "meanshift").
        precision (Optional[Precision]): Minimum required precision to be considered "ok".

    Raises:
        ValueError: If `strategy` is not provided in scan mode.
    """
    permutations = get_mass_permutations(decay=decay, identifier=identifier)

    rows = []  # Each row: (subdir, status, count or message)
    counts = {
        "ok": 0,
        "below_threshold": 0,
        "low_precision": 0,
        "missing": 0,
        "non_calculable": 0,
        "error": 0,
    }

    for xmass, smass, resolvable, _ in permutations:
        model = Model(name=model_name, masses={"X": xmass, "S": smass, "H": 125.09})
        subdir = model.mass_string
        decay_used = decay if resolvable else get_non_resolvable_decay(decay)

        try:
            status, info = get_mass_point_status(
                model_name=model_name,
                decay=decay_used,
                xmass=xmass,
                smass=smass,
                threshold=threshold,
                mode=mode,
                strategy=strategy,
                precision=precision
            )
        except Exception as e:
            status = "error"
            info = str(e)

        rows.append((subdir, status, info))
        counts[status] += 1

    total = sum(counts.values())

    # Print screen summary
    print("\n=== Mass List Completion Summary ===")
    print(f"Total mass points checked:   {total}")
    print(f"  Pass threshold:            {counts['ok']}")
    print(f"  Below threshold:           {counts['below_threshold']}")
    print(f"  Low precision:             {counts['low_precision']}")
    print(f"  Missing file:              {counts['missing']}")
    print(f"  Non-calculable (excluded): {counts['non_calculable']}")
    print(f"  Errors:                    {counts['error']}")

    # Write output file
    out_filename = os.path.join(output_dir(), "mass_list_counts.txt")
    with open(out_filename, "w") as out:
        out.write("# Mass List Completion Report\n\n")
        out.write(f"# Mode: {mode}\n")
        out.write(f"# Model: {model_name}\n")
        out.write(f"# Decay: {decay}\n")
        out.write(f"# Identifier: {identifier}\n")
        out.write(f"# Precision: {precision}\n\n")
        out.write(f"Total mass points checked:   {total}\n")
        out.write(f"  Pass threshold:            {counts['ok']}\n")
        out.write(f"  Below threshold:           {counts['below_threshold']}\n")
        out.write(f"  Low precision:             {counts['low_precision']}\n")
        out.write(f"  Missing file:              {counts['missing']}\n")
        out.write(f"  Non-calculable (excluded): {counts['non_calculable']}\n")
        out.write(f"  Errors:                    {counts['error']}\n\n")

        for category in counts:
            group = [r for r in rows if r[1] == category]
            out.write(f"--- {category} ({len(group)}) ---\n")
            for subdir, _, detail in group:
                if category in ["ok", "below_threshold"] and isinstance(detail, int):
                    out.write(f"  {subdir}: {detail}\n")
                elif category == "low_precision" and isinstance(detail, Precision):
                    out.write(f"  {subdir}: {detail}\n")
                elif category == "error":
                    out.write(f"  {subdir}: ERROR: {detail}\n")
                else:
                    out.write(f"  {subdir}\n")
            out.write("\n")

    print(f"\nDetailed results written to: {out_filename}")

def get_mass_point_status(model_name: str,
                          decay: str,
                          xmass: float,
                          smass: float,
                          threshold: int,
                          mode: str,
                          strategy: Optional[str] = None,
                          precision: Optional[Precision] = None
                          ) -> Tuple[str, Optional[Union[int,Precision]]]:
    """
    Check the scan or prescan status of a single (X, S) mass point.

    Args:
        model_name (str): Name of the scalar model.
        decay (str): Decay mode to use exactly as provided.
        xmass (float): X scalar mass (GeV).
        smass (float): S scalar mass (GeV).
        threshold (int): Minimum required number of points.
        mode (str): Either "prescan" or "scan".
        strategy (Optional[str]): Optimization strategy. Required if mode is "scan".
        precision (Optional[Precision]): Minimum required precision.

    Returns:
        Tuple[str, Optional[int]]:
            - Status: One of {"ok", "below_threshold", "low_precision", "missing", "non_calculable"}
            - Count of points if applicable (None for "missing" or "non_calculable")

    Raises:
        ValueError: If required parameters are missing or invalid.
        OSError / JSONDecodeError: If files are corrupt or unreadable.
    """
    model = Model(name=model_name, masses={"X": xmass, "S": smass, "H": 125.09})
    subdir = model.mass_string

    if not model.is_calculable:
        return "non_calculable", None

    if mode == "prescan":
        path = os.path.join(output_dir(), model.name, "prescan", subdir, f"{model.name}_prescan.tsv")
        if not os.path.isfile(path):
            return "missing", None
        count = count_tsv_points(path)
        return ("ok", count) if count >= threshold else ("below_threshold", count)

    elif mode == "scan":
        if strategy is None:
            raise ValueError("Scan mode requires a strategy.")
        path = os.path.join(output_dir(), model.name, "scan", decay, subdir,
                            strategy, f"run_metadata_{strategy}.json")
        if not os.path.isfile(path):
            return "missing", None
        with open(path, "r") as f:
            data = json.load(f)

        existing_precision_str: str = data.get("precision")
        # Handle missing or invalid precision from file
        if existing_precision_str is None:
            if precision is not None:
                return "low_precision", None  # Precision was requested, but missing in metadata
            prev_precision = None
        else:
            try:
                prev_precision = Precision.from_string(existing_precision_str)
            except ValueError:
                # If string is invalid or malformed, treat as too low to be safe
                return "low_precision", None
        # Now compare, if required
        if precision is not None and (prev_precision is None or prev_precision < precision):
            return "low_precision", prev_precision

        count = data.get("num_points", 0)
        return ("ok", count) if count >= threshold else ("below_threshold", count)

    else:
        raise ValueError(f"Invalid mode '{mode}'")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("--mode", required=True, choices=["prescan", "scan"], help="Which type of file to evaluate")
    parser.add_argument("-m", "--model", default="TRSMBroken", type=str, choices=supported_models, help="Model name")
    parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    parser.add_argument("-t", "--threshold", required=True, type=int, help="Point count threshold")
    parser.add_argument("-s", "--strategy", default="zoom", type=str, choices=['zoom','meanshift'], help="Optimization strategy (required for scan mode)")
    parser.add_argument("-p", "--precision", type=Precision.from_string, choices=list(Precision), default=Precision.MEDIUM, help="Precision level threshold")
    args = parser.parse_args()

    check_mass_list(
        model_name=args.model,
        decay=args.decay,
        identifier=args.identifier,
        threshold=args.threshold,
        mode=args.mode,
        strategy=args.strategy,
        precision=args.precision
    )
