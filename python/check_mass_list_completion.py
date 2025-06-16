#!/usr/bin/env python3

import os
import argparse
import json
import pandas as pd
from typing import Optional

from utils.tsv_utils import count_tsv_points
from mass_grid.mass_json_utils import get_mass_permutations
from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir

def check_mass_list_completion(model: str,
                                decay: str,
                                identifier: str,
                                threshold: int,
                                mode: str,
                                strategy: Optional[str] = None) -> None:
    """
    Checks prescan or scan point counts for all mass point permutations.

    Args:
        model (str): Theoretical model.
        decay (str): Decay mode.
        identifier (str): Set identifier.
        threshold (int): Minimum acceptable number of points.
        mode (str): Either "prescan" or "scan".
        strategy (Optional[str]): Required if mode is "scan".
    """
    permutations = get_mass_permutations(decay=decay,
                                         identifier=identifier)

    results = []
    missing = []

    for XMass, SMass, resolvable in permutations:
        decay_used = decay if resolvable else get_non_resolvable_decay(decay)
        subdir = f"X{int(XMass)}_S{int(SMass)}"

        if mode == "prescan":
            filepath = os.path.join(output_dir(), model, "prescan", subdir, f"{model}_prescan.tsv")
            if not os.path.isfile(filepath):
                missing.append(filepath)
                continue
            try:
                count = count_tsv_points(filepath)
                results.append((subdir, count))
            except Exception as e:
                print(f"[error] Failed to read TSV: {filepath}: {e}")

        elif mode == "scan":
            if strategy is None:
                raise ValueError("Scan mode requires --strategy.")
            filepath = os.path.join(output_dir(), model, "scan", decay_used, subdir, "summary_{}.json".format(strategy))
            if not os.path.isfile(filepath):
                missing.append(filepath)
                continue
            try:
                with open(filepath) as f:
                    data = json.load(f)
                count = len(data.get("points", []))
                results.append((subdir, count))
            except Exception as e:
                print("[error] Failed to read JSON: {}: {}".format(filepath, e))

    if not results:
        print("No valid files found.")
        return

    df = pd.DataFrame(results, columns=["Permutation", "PointCount"])
    df.sort_values("PointCount", ascending=False, inplace=True)
    below = df[df["PointCount"] < threshold]

    print("\n=== Summary ===")
    for _, row in df.iterrows():
        flag = " <-- BELOW THRESHOLD" if row["PointCount"] < threshold else ""
        print("{}: {}{}".format(row["Permutation"], row["PointCount"], flag))

    print(f"\n==> {len(below)} permutations are below the threshold of {threshold}.")
    if not below.empty:
        print("Below-threshold permutations:")
        for name in below["Permutation"]:
            print(f"  - {name}")

    if missing:
        print(f"\n==> {len(missing)} files missing:")
        for path in missing:
            print(f"  - {path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    parser.add_argument("-t", "--threshold", required=True, type=int, help="Point count threshold")
    parser.add_argument("--mode", required=True, choices=["prescan", "scan"], help="Which type of file to evaluate")
    parser.add_argument("-s", "--strategy", required=False, type=str, help="Scan strategy (required for scan mode)")

    args = parser.parse_args()

    check_mass_list_completion(
        model=args.model,
        decay=args.decay,
        identifier=args.identifier,
        threshold=args.threshold,
        mode=args.mode,
        strategy=args.strategy
    )
