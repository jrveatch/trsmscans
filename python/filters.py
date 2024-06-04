#!/usr/bin/env python3

import argparse

import numpy as np

from arrays import Arrays
import width
import bounds
import tsvutils

from masses import Masses

header_width = "filt_width"
header_bounds = "filt_bounds"

def applyFilters(filename,
                 maxwidth,
                 masses: Masses):

    # initialize filter columns
    initializeFilters(filename)

    # apply width filter
    nwidth = width.filterwidths(filename,maxwidth)

    # apply bounds filter
    nbounds = bounds.filterbounds(filename,masses)

    # get arrays from output file
    arrs = Arrays(filename)
    arrs.loadArrays()

    # find how many points pass both filters
    filt_width = arrs.data[header_width]
    filt_bounds = arrs.data[header_bounds]
    filt_total = np.multiply(filt_width,filt_bounds)
    npass = filt_total.sum()

    # return numbers of events passing each filter
    return nwidth, nbounds, npass

def initializeFilters(filename):

    # initialize both columns
    tsvutils.initializeColumn(filename=filename,
                              column_header=header_width,
                              value=1)
    tsvutils.initializeColumn(filename=filename,
                              column_header=header_bounds,
                              value=1)

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-f", "--filename", help="Name of file to apply filters to")
    argparser.add_argument("-w", "--maxwidth", default=0.15, type=float, help="Maximum allowed width for any scalar")
    args = argparser.parse_args()

    applyFilters(filename=args.filename,maxwidth=args.maxwidth)
