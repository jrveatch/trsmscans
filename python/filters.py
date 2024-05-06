
import os
import shutil
import argparse

import numpy as np

import arrays
import width
import bounds

from masses import Masses

def applyFilters(input_file,
                 maxwidth,
                 masses: Masses,
                 output_file=""):

    # initialize filter columns
    initializeFilters(input_file,output_file)

    # if no output file name is given, use input_file
    filename=output_file
    if not filename:
        filename=input_file

    # apply width filter
    nwidth = width.filterwidths(filename,maxwidth)

    # apply bounds filter
    nbounds = bounds.filterbounds(filename,masses)

    # get arrays from output file
    arrs = arrays.Arrays(filename)
    arrs.loadArrays()

    # find how many points pass both filters
    filt_width = arrs.data['filt_width']
    filt_bounds = arrs.data['filt_bounds']
    filt_total = np.multiply(filt_width,filt_bounds)
    npass = filt_total.sum()

    # return numbers of events passing each filter
    return nwidth, nbounds, npass

def initializeFilters(input_file,output_file=""):

    # filter column headers
    header_width = "filt_width"
    header_bounds = "filt_bounds"

    # check whether filt_width and filt_bounds columns exist
    has_filt_width = column_exists(input_file,"filt_width")
    has_filt_bounds = column_exists(input_file,"filt_bounds")

    # skip initialization if it is not needed
    if has_filt_width and has_filt_bounds:
        return

    # set up output file name
    outname = "temp.tsv"
    replacefile = True
    if output_file:
        outname = output_file
        replacefile = False

    with open(input_file, 'r') as f_in, open(outname, 'w') as f_out:
        
        # read the header
        header = f_in.readline().strip().split('\t')
        
        # add new column headers if needed
        if not has_filt_width:
            header.append(header_width)
        if not has_filt_bounds:
            header.append(header_bounds)
        
        # write the updated header to the output file
        f_out.write('\t'.join(header) + '\n')
        
        # iterate through each line in the input file
        for line in f_in:
            
            # split the line into columns
            columns = line.strip().split('\t')
            
            # append the new column data
            if not has_filt_width:
                columns.append('1')
            if not has_filt_bounds:
                columns.append('1')

            # write the updated line to the output file
            f_out.write('\t'.join(columns) + '\n')

    # replace the input file with the output file
    if replacefile:
        shutil.move(outname, input_file)
    # otherwise delete the input file
    else:
        os.remove(input_file)

def column_exists(input_file,column_header):

    with open(input_file, 'r') as f_in:
        # Read the header
        header = f_in.readline().strip().split('\t')
        # Check if the column header exists in the header
        return column_header in header

if __name__ == "__main__":

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-f", "--filename", help="Name of file to apply filters to")
    argparser.add_argument("-w", "--widthmax", default=0.15, type=float, help="Maximum allowed width for any scalar")
    args = vars(argparser.parse_args())

    # filename
    filename = args["filename"]

    # maximum allowed width
    maxwidth = args["widthmax"]

    applyFilters(input_file=filename,maxwidth=maxwidth)
