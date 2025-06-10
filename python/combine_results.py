#!/usr/bin/env python3

import argparse
import os

from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir
from utils.mass_permutations import get_mass_permutations
from utils.tsv_utils import parse_tsv_file

def combine_results(model: str,
                    decay: str,
                    identifier: str,
                    optimization: str) -> None:
    """
    Combines results from multiple mass points into a single summary file.

    Args:
        model (str): Name of the theoretical model.
        decay (str): Decay mode.
        identifier (str): Identifier to specify which set of mass points to use.
        optimization (str): Optimization strategy used in the scan, e.g., 'zoom' or 'meanshift'.
    """

    permutations = get_mass_permutations(decay=decay, identifier=identifier)

    combination_file_name = os.path.join(output_dir(),model,"scan",decay,f"{decay}_{identifier}_combination.tsv")
    tsv_combination_file_name = os.path.join(output_dir(),model,"scan",decay,f"{decay}_{identifier}_tsv_combination.tsv")

    try:
        for XMass, SMass, resolvable in permutations:

            # Get the directory for the mass point
            directory = os.path.join(output_dir(),model,"scan",decay,f"X{int(XMass)}_S{int(SMass)}")

            # If mass point isn't resolvable, use the non-resolvable decay
            if not resolvable:
                directory = os.path.join(output_dir(),model,"scan",get_non_resolvable_decay(decay),f"X{int(XMass)}_S{int(SMass)}")
            if not os.path.isdir(directory):
                print(f"Directory {directory} does not exist. Skipping.")
                continue

            # Get list of all .tsv files
            tsv_files = [f for f in os.listdir(directory) if f.endswith('.tsv')]

            # Process summary .tsv files in the directory
            for file in tsv_files:

                # Skip files that don't start with the correct prefix
                if not file.startswith(f"summary_{optimization}"):
                    continue

                # Combine tsv summary files
                if file.startswith(f'summary_{optimization}_tsv'):
                    write_combination_row(
                        input_path=os.path.join(directory, file),
                        output_path=tsv_combination_file_name,
                        skip_first_col=True
                    )

                # Combine summary files
                else:
                    write_combination_row(
                        input_path=os.path.join(directory, file),
                        output_path=combination_file_name,
                        header_prefix="XMass\tSMass\tHMass\t",
                        row_prefix=f"{float(XMass)}\t{float(SMass)}\t125.09\t",
                        skip_last_col=True
                    )

    except Exception as e:
        print(f"Error writing to output file {combination_file_name}: {e}")

def write_combination_row(input_path: str,
                          output_path: str,
                          header_prefix: str = "",
                          row_prefix: str = "",
                          skip_first_col: bool = False,
                          skip_last_col: bool = False) -> None:
    """
    Appends the last row of a TSV file to an output file, writing headers if needed.

    Args:
        input_path (str): Path to the input TSV file.
        output_path (str): Path to the output combined TSV file.
        header_prefix (str): Prefix to prepend to the header row.
        row_prefix (str): Prefix to prepend to the data row.
        skip_first_col (bool): Whether to exclude the first column from input.
        skip_last_col (bool): Whether to exclude the last column from input.
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

    write_header = not os.path.isfile(output_path) or os.stat(output_path).st_size == 0

    with open(output_path, 'a') as output_file:
        if write_header:
            output_file.write(header_prefix + "\t".join(headers) + "\n")

        last_row_values = [rows[-1].get(h, "") for h in headers]
        output_file.write(row_prefix + "\t".join(last_row_values) + "\n")

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    args = arg_parser.parse_args()

    combine_results(model=args.model,
                    decay=args.decay,
                    identifier=args.identifier,
                    optimization=args.strategy)

    # TODO: Add function to plot combined results
