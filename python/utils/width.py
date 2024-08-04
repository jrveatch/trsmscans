#!/usr/bin/env python3

import numpy as np

from arrays import Arrays
from utils import tsvutils

def filter_widths(filename: str,
                  maxwidth: float) -> int:

    # TODO: accept different widths for each H

    # initialize column in case it doesn't exist
    tsvutils.initializeColumn(filename=filename,
                              column_header="filt_width",
                              value=1)

    # load in arrays from .tsv file
    arrs = Arrays(filename)
    arrs.load_arrays()

    # get arrays of widths
    width_H1 = np.divide(arrs.get_array('w_H1'),arrs.get_array('mH1'))
    width_H2 = np.divide(arrs.get_array('w_H2'),arrs.get_array('mH2'))
    width_H3 = np.divide(arrs.get_array('w_H3'),arrs.get_array('mH3'))

    # check whether each width is below the maxwidth
    mask1 = width_H1 < maxwidth
    mask2 = width_H2 < maxwidth
    mask3 = width_H3 < maxwidth

    # create the product of the 3 masks
    mask = mask1 & mask2 & mask3

    # create array of 0 and 1 based on mask
    filt_width = mask.astype(int)

    # overwrite filt_width array with new array
    arrs.set_array('filt_width',filt_width)

    # write new data to file
    arrs.write_file(filename)

    # number of entries that pass
    npass = filt_width.sum()
    return npass
