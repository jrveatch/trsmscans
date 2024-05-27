
import os
import subprocess

# function to get number of points in a file
# returns 0 if file does not exist
# otherwise returns number of existing points in file
def countPointsInTSV(filename):

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
def saveTSVOutput(inputfile,outputfile):

    # get number of points already in output file
    nexisting = countPointsInTSV(outputfile)

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
