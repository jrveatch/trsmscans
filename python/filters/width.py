#!/usr/bin/env python3

import numpy as np

from utils.arrays import Arrays
from utils import tsvutils

from utils.config_loader import ConfigLoader

def filter_widths(file_name: str,
                  config_loader: 'ConfigLoader') -> int:

    # TODO: accept different widths for each H

    # initialize column in case it doesn't exist
    tsvutils.initialize_column(file_name=file_name,
                               column_header="filt_width",
                               value=1)

    # load in arrays from .tsv file
    arrs = Arrays(file_name)

    # get arrays of widths
    width_H1 = np.divide(arrs.get_array('w_H1'),arrs.get_array('mH1'))
    width_H2 = np.divide(arrs.get_array('w_H2'),arrs.get_array('mH2'))
    width_H3 = np.divide(arrs.get_array('w_H3'),arrs.get_array('mH3'))

    # get max_width from config file
    try:
        max_width_H1: float = config_loader.get('width', 'max_width_H1')
        max_width_H2: float = config_loader.get('width', 'max_width_H2')
        max_width_H3: float = config_loader.get('width', 'max_width_H3')
    except KeyError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

    # check whether each width is below the max width
    mask1 = width_H1 < max_width_H1
    mask2 = width_H2 < max_width_H2
    mask3 = width_H3 < max_width_H3

    # create the product of the 3 masks
    mask = mask1 & mask2 & mask3

    # create array of 0 and 1 based on mask
    filt_width = mask.astype(int)

    # overwrite filt_width array with new array
    arrs.set_array('filt_width',filt_width)

    # write new data to file
    arrs.write_file(file_name)

    # number of entries that pass
    npass = filt_width.sum()
    return npass
