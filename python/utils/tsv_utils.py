
# standard libraries
import csv
import logging
import os
import subprocess

# get logger
logger = logging.getLogger(__name__)

def count_tsv_points(file_name: str) -> int:
    """
    Count the number of data rows (excluding header) in a .tsv file.

    This function uses `wc -l` to count the number of lines in the file and subtracts one for the header.

    Args:
        file_name (str): Path to the .tsv file.

    Returns:
        int: The number of data rows. Returns 0 if the file doesn't exist or if an error occurs.
    """

    # if file doesn't exist, return -1
    if not os.path.exists(file_name):
        return 0

    # run wc -l to get the number of lines
    result = subprocess.run(["wc", "-l", file_name], capture_output=True, text=True)

    # get output from wc -l
    output = result.stdout.strip()

    # get the number of previously scanned points
    num_points = int(output.split()[0]) - 1

    # return number of points
    return num_points

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
        os.rename(input_file,output_file)
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

def sort_tsv_file(filename: str,
                  sort_column: str = "xbmax") -> None:
    """
    Sort a .tsv file in-place based on the values in a specified column.

    If the values in the sort column can be interpreted as floats, a numeric sort is used.
    Otherwise, a string-based sort is applied.

    Args:
        filename (str): Path to the .tsv file to sort.
        sort_column (str, optional): The column name to sort by. Defaults to "xbmax".

    Raises:
        ValueError: If the file is empty or lacks a valid header.
        KeyError: If the specified sort column is not present in all rows.
    """

    # Read the TSV file
    with open(filename, newline='') as f:
        reader = csv.DictReader(f, delimiter='\t')
        rows = list(reader)
        headers = reader.fieldnames
    
    if headers is None:
        raise ValueError(f"Could not read headers from {filename}")

    # Make sure sort column exists
    if not all(sort_column in row for row in rows):
        raise KeyError(f"Sort column '{sort_column}' missing in some rows")

    # Sort the rows by the specified column (converted to float if needed)
    try:
        rows.sort(key=lambda row: float(row[sort_column]))
    except ValueError:
        rows.sort(key=lambda row: row[sort_column])  # Fallback to string sort if not numeric

    # Write the sorted data back to the same file
    with open(filename, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers, delimiter='\t')
        writer.writeheader()
        writer.writerows(rows)
