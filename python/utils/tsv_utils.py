
# standard libraries
import logging
import os
import subprocess

# get logger
logger = logging.getLogger(__name__)

# function to get number of points in a file
# returns 0 if file does not exist
# otherwise returns number of existing points in file
def count_tsv_points(file_name: str) -> int:

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

# function to save output tsv file
def save_tsv_output(input_file: str,
                    output_file: str) -> None:

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
