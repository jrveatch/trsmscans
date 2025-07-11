#!/usr/bin/env python3

import argparse
import os

from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir
from mass_grid.mass_json_utils import get_mass_permutations
from utils.model import Model, supported_models
from utils.tsv_utils import parse_tsv_file

HIGGS_MASS = 125.09

def combine_results(model_name: str,
                    decay: str,
                    identifier: str,
                    optimization: str) -> None:
    """
    Combines results from multiple mass points into a single summary file.

    Args:
        model_name (str): Name of the theoretical model.
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.
        optimization (str): Optimization strategy used in the scan, e.g., 'zoom' or 'meanshift'.
    """

    permutations = get_mass_permutations(decay=decay,
                                         identifier=identifier)

    scan_dir = os.path.join(output_dir(), model_name, "scan")
    comb_dir = os.path.join(output_dir(), model_name, "combination")
    os.makedirs(comb_dir, exist_ok=True)
    combination_file_name = os.path.join(comb_dir, f"{decay}_{identifier}_combination.tsv")
    tsv_combination_file_name = os.path.join(comb_dir, f"{decay}_{identifier}_tsv_combination.tsv")

    # Clear output files if they already exist
    open(combination_file_name, 'w').close()
    open(tsv_combination_file_name, 'w').close()

    non_calculable = 0
    for XMass, SMass, resolvable, _ in permutations:

        model = Model(name=model_name, masses={"H": 125.09, "S": SMass, "X": XMass})
        if not model.is_calculable:
            non_calculable += 1
            continue

        # Get the directory for the mass point
        decay_used = decay if resolvable else get_non_resolvable_decay(decay)
        directory = os.path.join(scan_dir, decay_used, f"X{int(XMass)}_S{int(SMass)}")

        # Skip if the directory does not exist
        if not os.path.isdir(directory):
            print(f"Directory {directory} does not exist. Skipping.")
            continue

        # Process summary .tsv files in the directory and skip if they don't match the expected naming convention
        for file in (f for f in os.listdir(directory) if is_summary_file(f, optimization)):

            # Combine tsv summary files
            if file.startswith(f"summary_{optimization}_tsv"):
                write_combination_row(
                    input_path=os.path.join(directory, file),
                    output_path=tsv_combination_file_name,
                    optimization=optimization,
                    skip_first_col=True
                )

            # Combine summary files
            else:
                write_combination_row(
                    input_path=os.path.join(directory, file),
                    output_path=combination_file_name,
                    optimization=optimization,
                    header_prefix="XMass\tSMass\tHMass\t",
                    row_prefix=f"{float(XMass)}\t{float(SMass)}\t{HIGGS_MASS}\t",
                    skip_last_col=True,
                    add_precision=True
                )

    print(f"Done combining {len(permutations) - non_calculable} results for {decay} {identifier} mass list.")
    print(f"Skipped {non_calculable} non-calculable mass points.")

def write_combination_row(input_path: str,
                          output_path: str,
                          optimization: str,
                          header_prefix: str = "",
                          row_prefix: str = "",
                          skip_first_col: bool = False,
                          skip_last_col: bool = False,
                          add_precision: bool = False) -> None:
    """
    Appends the last row of a TSV file to an output file, writing headers if needed.

    Args:
        input_path (str): Path to the input TSV file.
        output_path (str): Path to the output combined TSV file.
        optimization (str): Optimization strategy used in the scan, e.g., 'zoom' or 'meanshift'.
        header_prefix (str): Prefix to prepend to the header row.
        row_prefix (str): Prefix to prepend to the data row.
        skip_first_col (bool): Whether to exclude the first column from input.
        skip_last_col (bool): Whether to exclude the last column from input.
        add_precision (bool): Whether to include the scan precision as a new column.
    """
    try:
        headers, rows = parse_tsv_file(input_path,
                                       skip_first_col=skip_first_col,
                                       skip_last_col=skip_last_col)
    except ValueError:
        print(f"{input_path} is empty or malformed. Skipping.")
        return
    except Exception as e:
        print(f"Error reading or processing {input_path}: {e}")
        return

    if not rows:
        print(f"No data rows in {input_path}. Skipping.")
        return

    try:
        write_header = os.path.getsize(output_path) == 0
    except FileNotFoundError:
        write_header = True

    precision_str = ""
    if add_precision:
        try:
            json_file = os.path.join(os.path.dirname(input_path), optimization, f"run_metadata_{optimization}.json")
            with open(json_file, 'r') as jf:
                import json
                config = json.load(jf)
                precision_str = str(config.get("precision", ""))
        except Exception as e:
            print(f"Could not read precision from {json_file}: {e}")

    with open(output_path, 'a') as output_file:
        if write_header:
            header_line = header_prefix + "\t".join(headers)
            if add_precision:
                header_line += "\tprecision"
            output_file.write(header_line + "\n")

        last_row_values = [rows[-1].get(h, "") for h in headers]
        if add_precision:
            last_row_values.append(precision_str)
        output_file.write(row_prefix + "\t".join(last_row_values) + "\n")

def is_summary_file(file_name: str,
                    optimization: str) -> bool:
    """
    Checks if a file is a summary file for the specified optimization strategy.
    Args:
        file_name (str): Name of the file to check.
        optimization (str): Optimization strategy used in the scan, e.g., 'zoom' or 'meanshift'.
    Returns:
        bool: True if the file is a summary file for the specified optimization strategy, False otherwise.
    """
    return file_name.endswith(".tsv") and file_name.startswith(f"summary_{optimization}")

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", default="TRSMBroken", type=str, choices=supported_models, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    arg_parser.add_argument("-s", "--strategy", default="zoom", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    args = arg_parser.parse_args()

    combine_results(model_name=args.model,
                    decay=args.decay,
                    identifier=args.identifier,
                    optimization=args.strategy)
