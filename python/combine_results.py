#!/usr/bin/env python3

import argparse
import os

from utils.decay_utils import get_non_resolvable_decay
from utils.file_utils import output_dir
from utils.mass_permutations import get_mass_permutations

def combine_results(model: str,
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

    # Initialize a variable for headers
    combination_headers_written = False
    tsv_combination_headers_written = False

    combination_file_name = output_dir() + f"{model}/scan/{decay}/{decay}_{identifier}_combination.tsv"
    tsv_combination_file_name = output_dir() + f"{model}/scan/{decay}/{decay}_{identifier}_tsv_combination.tsv"

    try:
        with open(combination_file_name, 'w') as combination_file, open(tsv_combination_file_name, 'w') as tsv_combination_file:
            for XMass, SMass, resolvable in permutations:
                # Get the directory for the mass point
                directory = output_dir() + f"{model}/scan/{decay}/X{XMass}_S{SMass}/"
                # If mass point isn't resolvable, use the non-resolvable decay
                if not resolvable:
                    directory = output_dir() + f"{model}/scan/{get_non_resolvable_decay(decay)}/X{XMass}_S{SMass}/"
                if not os.path.isdir(directory):
                    print(f"Directory {directory} does not exist. Skipping.")
                    continue

                # Get list of all .tsv files
                tsv_files = [f for f in os.listdir(directory) if f.endswith('.tsv')]
                
                # Process summary .tsv files in the directory
                for summary_file in tsv_files:
                    if not summary_file.startswith('zoom_summary') or summary_file.startswith("zoom_summary_tsv"):
                        continue  # Skip files that don't start with "scan_summary"
                    summary_path = os.path.join(directory, summary_file)
                    try:
                        with open(summary_path, 'r') as summary:
                            lines = summary.readlines()
                            if not lines:
                                print(f"{summary_path} is empty. Skipping.")
                                continue
                            
                            # Extract headers and remove the last column
                            file_headers = lines[0].strip().split('\t')[:-1]  # Exclude the last column
                            last_line = lines[-1].strip().split('\t')[:-1]  # Exclude the last column

                            # Write headers to the output file if not already written
                            if not combination_headers_written:
                                new_headers = f"XMass\tSMass\tHMass\t" + "\t".join(file_headers)
                                combination_file.write(new_headers + "\n")
                                combination_headers_written = True

                            # Write data row to the output file
                            combination_file.write(f"{float(XMass)}\t{float(SMass)}\t125.09\t" + "\t".join(last_line) + "\n")
                    except Exception as e:
                        print(f"Error reading or processing {summary_path}: {e}")
                
                # Process tsv summary .tsv files in the directory
                for tsv_summary_file in tsv_files:
                    if not tsv_summary_file.startswith('summary_zoom_tsv'):
                        continue  # Skip files that don't start with "scan_tsv_summary"
                    tsv_summary_path = os.path.join(directory, tsv_summary_file)
                    try:
                        with open(tsv_summary_path, 'r') as tsv_summary:
                            lines = tsv_summary.readlines()
                            if not lines:
                                print(f"{tsv_summary_path} is empty. Skipping.")
                                continue
                            
                            # Extract headers and remove the last column
                            file_headers = lines[0].strip().split('\t')[1:]  # Exclude the first column
                            last_line = lines[-1].strip().split('\t')[1:]  # Exclude the first column

                            # Write headers to the output file if not already written
                            if not tsv_combination_headers_written:
                                tsv_combination_file.write("\t".join(file_headers) + "\n")
                                tsv_combination_headers_written = True

                            # Write data row to the output file
                            tsv_combination_file.write("\t".join(last_line) + "\n")
                    except Exception as e:
                        print(f"Error reading or processing {tsv_summary_path}: {e}")

    except Exception as e:
        print(f"Error writing to output file {combination_file}: {e}")

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-i", "--identifier", required=True, type=str, help="Set identifier")
    args = arg_parser.parse_args()

    combine_results(model=args.model,
                    decay=args.decay,
                    identifier=args.identifier)
    
    # TODO: Add function to plot combined results
