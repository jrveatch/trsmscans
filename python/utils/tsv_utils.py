
# standard libraries
import csv
import logging
import os
import shutil
from typing import List, Dict, Optional, Tuple

from utils.math_utils import round_sig
from utils.model import Model
from utils.point import Point

# get logger
logger = logging.getLogger(__name__)

def count_tsv_points(file_name: str) -> int:
    """
    Count the number of data rows (excluding header) in a .tsv file.

    Args:
        file_name (str): Path to the .tsv file.

    Returns:
        int: Number of data rows (0 if file missing or empty).
    """
    try:
        with open(file_name, 'r') as f:
            return max(0, sum(1 for _ in f) - 1)
    except Exception:
        return 0

def save_tsv_output(input_file: str,
                    output_file: str) -> None:
    """
    Merge the contents of an input .tsv file into an output .tsv file, renumbering the index column.

    If the output file does not exist or is empty, the input file is simply renamed.
    If the output file exists, the input is appended (skipping its header), and index values are
    updated to ensure uniqueness.

    Args:
        input_file (str): Path to the source .tsv file.
        output_file (str): Path to the destination .tsv file.
    """

    # normalize paths to absolute paths for comparison
    input_file = os.path.abspath(input_file)
    output_file = os.path.abspath(output_file)

    # check if input_file and output_file point to the same file
    if input_file==output_file:
        logger.warning(f"Input file path '{input_file}' and output file path '{output_file}' are the same.")
        return

    # get number of points already in output file
    num_existing = count_tsv_points(output_file)

    # if output file doesn't exist or is empty, simply rename input file
    if num_existing <= 0:
        shutil.move(input_file,output_file)
        return

    # otherwise append the contents of input_file to output_file
    with open(input_file,'r') as source_file:

        # skip the first line to avoid writing headers multiple times
        next(source_file)

        # open output .tsv file for appending
        with open(output_file,'a') as destination_file:

            # get each line in the new .tsv file
            for count, line in enumerate(source_file):

                # replace the index with a unique value
                parts = line.strip().split('\t')
                parts[0] = str(count + num_existing)

                # append each line to final .tsv file
                destination_file.write('\t'.join(parts) + '\n')

    # delete input .tsv file
    os.remove(input_file)

def sort_tsv_file(file_name: str,
                  sort_column: str = "xb") -> None:
    """
    Sort a .tsv file in-place based on the values in a specified column.

    If the values in the sort column can be interpreted as floats, a numeric sort is used.
    Otherwise, a string-based sort is applied.

    Args:
        file_name (str): Path to the .tsv file to sort.
        sort_column (str, optional): The column name to sort by. Defaults to "xb".

    Raises:
        ValueError: If the file is empty or lacks a valid header.
        KeyError: If the specified sort column is not present in all rows.
    """

    # Use the new parser to get headers and rows
    headers, rows = parse_tsv_file(file_name)

    # Make sure sort column exists
    if not all(sort_column in row for row in rows):
        raise KeyError(f"Sort column '{sort_column}' missing in some rows")

    # Sort the rows by the specified column (converted to float if needed)
    try:
        rows.sort(key=lambda row: float(row[sort_column]))
    except ValueError:
        rows.sort(key=lambda row: row[sort_column]) # Fallback to string sort if not numeric

    # Write the sorted data back to the same file
    with open(file_name, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)

def parse_tsv_file(file_name: str,
                   skip_first_col: bool = False,
                   skip_last_col: bool = False) -> Tuple[List[str], List[Dict[str, str]]]:
    """
    Parses a .tsv file and returns the header and data rows.

    Args:
        file_name (str): Path to the .tsv file to parse.
        skip_first_col (bool): If True, skips the first column in the header and data.
        skip_last_col (bool): If True, skips the last column in the header and data.

    Returns:
        Tuple[List[str], List[Dict[str, str]]]: A tuple containing the header as a list of strings
        and the data rows as a list of dictionaries where keys are column names.

    Raises:
        ValueError: If the file is empty or headers cannot be read.
    """
    try:
        with open(file_name, 'r') as f:
            reader = csv.reader(f, delimiter='\t')
            all_lines = list(reader)

        if not all_lines or not all_lines[0]:
            raise ValueError(f"No headers found in file: {file_name}")

        # Adjust headers
        headers: List[str] = all_lines[0]
        if skip_first_col:
            headers = headers[1:]
        if skip_last_col:
            headers = headers[:-1]

        if not headers:
            raise ValueError(f"Headers are empty after column exclusion in file: {file_name}")

        # Adjust rows
        adjusted_rows: List[Dict[str, str]] = []
        for row in all_lines[1:]:
            if skip_first_col:
                row = row[1:]
            if skip_last_col:
                row = row[:-1]
            adjusted_rows.append(dict(zip(headers, row)))

        return headers, adjusted_rows

    except Exception as e:
        logger.error(f"Failed to parse .tsv file {file_name}: {e}")
        raise

def initialize_summary_file(file_name: str,
                            model: Model,
                            id_header: Optional[str] = None) -> None:
    """
    Creates a summary file with a header line with columns for `xb` and the model's parameters.

    If `id_header` is provided, it is appended as the final column header.

    Args:
        file_name (str): Path to the file where the point should be written.
        model (Model): Model used to get parameter names for column headers.
        id_header (Optional[str]): Iteration identifier to append as the final column header.
    """
    header = "xb" + "".join(f"\t{parameter}" for parameter in model.all_parameter_names)
    if id_header is not None:
        header += f"\t{id_header}"
    header += "\n"
    with open(file_name, 'w') as file:
        file.write(header)

def write_point_to_summary_file(file_name: str,
                                point: Point,
                                identifier: Optional[str] = None) -> None:
    """
    Appends a formatted line representing the given point to the specified summary file.

    The line includes the `xb` value followed by the point's parameter values,
    all formatted using `round_sig`, and separated by tabs. If `identifier` is provided,
    it is appended as the final column.

    Args:
        file_name (str): Path to the file where the point should be written.
        point (Point): The point containing `xb` and parameter values.
        identifier (Optional[str]): Iteration identifier to append as the final column.
    """
    content = f"{point.format_xb()}" + "".join(
        f"\t{round_sig(val)}" for val in point.parameter_values.values()
    )
    if identifier is not None:
        content += f"\t{identifier}"
    content += "\n"
    with open(file_name, 'a') as f:
        f.write(content)
