
import os
import shutil

import numpy as np

import arrays
import width
import bounds

def applyFilters(input_file,maxwidth,output_file=""):

    # initialize filter columns
    initializeFilters(input_file,output_file)

    # apply width filter
    nwidth = width.filterwidths(output_file,maxwidth)

    # apply bounds filter
    nbounds = bounds.filterbounds(output_file)

    # get arrays from output file
    arrs = arrays.Arrays(output_file)
    arrs.loadArrays()

    # find how many points pass both filters
    filt_width = arrs.data['filt_width']
    filt_bounds = arrs.data['filt_bounds']
    filt_total = np.multiply(filt_width,filt_bounds)
    npass = filt_total.sum()

    return nwidth, nbounds, npass

def initializeFilters(input_file,output_file=""):

    # filter column headers
    header_width = "filt_width"
    header_bounds = "filt_bounds"

    # check whether filt_width and filt_bounds columns exist
    has_filt_width = column_exists(input_file,"filt_width")
    has_filt_bounds = column_exists(input_file,"filt_bounds")

    # print to screen if columns already exist
    if has_filt_width:
        print(input_file,"already has",header_width,"column. Skipping initialization.")
    if has_filt_bounds:
        print(input_file,"already has",header_bounds,"column. Skipping initialization.")

    if has_filt_width and has_filt_bounds:
        print("Nothing left to initialize...")
        return

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
    else:
        os.remove(input_file)

def column_exists(input_file,column_header):

    with open(input_file, 'r') as f_in:
        # Read the header
        header = f_in.readline().strip().split('\t')
        # Check if the column header exists in the header
        return column_header in header
