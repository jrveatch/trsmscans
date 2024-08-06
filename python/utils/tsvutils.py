
import os
import shutil
import subprocess

# function to get number of points in a file
# returns 0 if file does not exist
# otherwise returns number of existing points in file
def count_tsv_points(filename: str) -> int:

    # if file doesn't exist, return -1
    if not os.path.exists(filename):
        return 0

    # run wc -l to get the number of lines
    result = subprocess.run(["wc", "-l", filename], capture_output=True, text=True)

    # get output from wc -l
    output = result.stdout.strip()

    # get the number of previously scanned points
    npoints = int(output.split()[0]) - 1

    # return number of points
    return npoints

# function to save output tsv file
def save_tsv_output(inputfile: str,
                    outputfile: str) -> None:

    # normalize paths to absolute paths for comparison
    inputfile = os.path.abspath(inputfile)
    outputfile = os.path.abspath(outputfile)
    
    # check if inputfile and outputfile point to the same file
    if inputfile==outputfile:
        print(f"Error: Input file path '{inputfile}' and output file path '{outputfile}' are the same.")
        return

    # get number of points already in output file
    nexisting = count_tsv_points(outputfile)

    # if output file doesn't exist or is empty, simply rename input file
    if nexisting <= 0:
        os.rename(inputfile,outputfile)
        return

    # otherwise append the contents of inputfile to outputfile
    with open(inputfile,'r') as source_file:

        # skip the first line to avoid writing headers multiple times
        next(source_file)

        # open output .tsv file for appending
        with open(outputfile,'a') as destination_file:

            # get each line in the new .tsv file
            for count, line in enumerate(source_file):

                # replace the index with a unique value
                parts = line.strip().split('\t')
                parts[0] = str(count + nexisting)

                # append each line to final .tsv file
                destination_file.write('\t'.join(parts) + '\n')

    # delete input .tsv file
    os.remove(inputfile)

    # return after a successful run
    return

# function to check whether a column already exists in file
def column_exists(filename: str,
                  column_header: str) -> bool:

    with open(filename, 'r') as f_in:
        # read the header
        header = f_in.readline().strip().split('\t')
        # check if the column header exists in the header
        return column_header in header

# function to add and initialize columns
# TODO: Rework this to accept a list of columns and values
def initialize_column(filename: str,
                      column_header: str,
                      value: float) -> None:

    # temp output filename
    temp_file = "temp.tsv"

    # return if column already exists
    if column_exists(filename=filename,column_header=column_header):
        return

    with open(filename, 'r') as f_in, open(temp_file, 'w') as f_out:
        
        # read the header
        header = f_in.readline().strip().split('\t')
        
        # add new column header
        header.append(column_header)
        
        # write the updated header to the output file
        f_out.write('\t'.join(header) + '\n')
        
        # iterate through each line in the input file
        for line in f_in:
            
            # split the line into columns
            columns = line.strip().split('\t')
            
            # append the new column data
            columns.append(str(value))

            # write the updated line to the output file
            f_out.write('\t'.join(columns) + '\n')

    # replace the input file with the temp file
    shutil.move(temp_file, filename)
