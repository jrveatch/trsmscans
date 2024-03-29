
import numpy as np

import arrays

import filters

def filterwidths(filename, maxwidth):

    # TODO: accept different widths for each H

    # check whether filt_width column exists, if not initialize it
    if not filters.column_exists(filename,"filt_width"):
        filters.initializeFilters(filename)

    # load in arrays from .tsv file
    arrs = arrays.Arrays(filename)
    arrs.loadArrays()

    # get arrays of widths
    width_H1 = np.divide(arrs.getArray('w_H1'),arrs.getArray('mH1'))
    width_H2 = np.divide(arrs.getArray('w_H2'),arrs.getArray('mH2'))
    width_H3 = np.divide(arrs.getArray('w_H3'),arrs.getArray('mH3'))

    # check whether each width is below the maxwidth
    mask1 = width_H1 < maxwidth
    mask2 = width_H2 < maxwidth
    mask3 = width_H3 < maxwidth

    # create the product of the 3 masks
    mask = mask1 & mask2 & mask3

    # create array of 0 and 1 based on mask
    filt_width = mask.astype(int)

    # overwrite filt_width array with new array
    arrs.setArray('filt_width',filt_width)

    # write new data to file
    arrs.writeFile(filename)

    # number of entries that pass
    npass = filt_width.sum()
    return npass
