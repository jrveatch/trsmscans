#!/usr/bin/env python3

import os
import argparse
import json
from typing import Optional

from utils.tsv_utils import count_tsv_points
from mass_grid.mass_json_utils import get_mass_permutations
from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir

def check_mass_list(model: str,
                    decay: str,
                    identifier: str,
                    threshold: int,
                    mode: str,
                    strategy: Optional[str] = None) -> None:
    """
    Checks prescan or scan point counts for all mass point permutations.

    Writes results to a temporary TSV file and prints a summary to the screen.
    """
    permutations = get_mass_permutations(decay=decay, identifier=identifier)

    rows = []
    counts = {
        "ok": 0,
        "below_threshold": 0,
        "missing": 0,
        "non_calculable": 0
    }

    for XMass, SMass, resolvable in permutations:
        subdir = f"X{int(XMass)}_S{int(SMass)}"

        if XMass >= 3000:
            rows.append((subdir, "non_calculable", ""))
            counts["non_calculable"] += 1
            continue

        decay_used = decay if resolvable else get_non_resolvable_decay(decay)

        if mode == "prescan":
            filepath = os.path.join(output_dir(), model, "prescan", subdir, f"{model}_prescan.tsv")
            if not os.path.isfile(filepath):
                rows.append((subdir, "missing", ""))
                counts["missing"] += 1
                continue
            try:
                count = count_tsv_points(filepath)
                if count < threshold:
                    rows.append((subdir, "below_threshold", count))
                    counts["below_threshold"] += 1
                else:
                    rows.append((subdir, "ok", count))
                    counts["ok"] += 1
            except Exception as e:
                rows.append((subdir, "error", str(e)))

        elif mode == "scan":
            if strategy is None:
                raise ValueError("Scan mode requires --strategy.")
            filepath = os.path.join(output_dir(), model, "scan", decay_used, subdir, f"summary_{strategy}.json")
            if not os.path.isfile(filepath):
                rows.append((subdir, "missing", ""))
                counts["missing"] += 1
                continue
            try:
                with open(filepath, "r") as f:
                    data = json.load(f)
                count = len(data.get("points", []))
                if count < threshold:
                    rows.append((subdir, "below_threshold", count))
                    counts["below_threshold"] += 1
                else:
                    rows.append((subdir, "ok", count))
                    counts["ok"] += 1
            except Exception as e:
                rows.append((subdir, "error", str(e)))

    total = sum(counts.values())

    # Print screen summary
    print("\n=== Mass List Completion Summary ===")
    print(f"Total mass points checked:   {total}")
    print(f"  Pass threshold:            {counts['ok']}")
    print(f"  Below threshold:           {counts['below_threshold']}")
    print(f"  Missing file:              {counts['missing']}")
    print(f"  Non-calculable (excluded): {counts['non_calculable']}")

    # Write human-readable block summary to file
    out_filename = os.path.join(output_dir(), "mass_list_counts.txt")
    with open(out_filename, "w") as out:
        out.write("# Mass List Completion Report\n\n")
        out.write(f"# Mode: {mode}\n")
        out.write(f"# Model:: {model}\n")
        out.write(f"# Decay: {decay}\n")
        out.write(f"# Identifier: {identifier}\n\n")
        out.write(f"Total mass points checked:   {total}\n")
        out.write(f"  Pass threshold:            {counts['ok']}\n")
        out.write(f"  Below threshold:           {counts['below_threshold']}\n")
        out.write(f"  Missing file:              {counts['missing']}\n")
        out.write(f"  Non-calculable (excluded): {counts['non_calculable']}\n\n")

        for category in ["ok", "below_threshold", "missing", "non_calculable"]:
            group = [r for r in rows if r[1] == category]
            out.write(f"--- {category} ({len(group)}) ---\n")
            for name, _, count in group:
                if category in ["ok", "below_threshold"]:
                    out.write(f"  {name}: {count}\n")
                else:
                    out.write(f"  {name}\n")
            out.write("\n")

    print(f"\nDetailed results written to: {out_filename}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    parser.add_argument("-t", "--threshold", required=True, type=int, help="Point count threshold")
    parser.add_argument("--mode", required=True, choices=["prescan", "scan"], help="Which type of file to evaluate")
    parser.add_argument("-s", "--strategy", required=False, type=str, help="Scan strategy (required for scan mode)")

    args = parser.parse_args()

    check_mass_list(
        model=args.model,
        decay=args.decay,
        identifier=args.identifier,
        threshold=args.threshold,
        mode=args.mode,
        strategy=args.strategy
    )
