#!/usr/bin/env python3

from utils.arrays import Arrays
from utils.tsv_utils import initialize_column

from utils.masses import Masses

from utils.config_loader import ConfigLoader

def filter_widths(file_name: str,
                  masses: Masses,
                  config_loader: 'ConfigLoader') -> int:

    # initialize column in case it doesn't exist
    initialize_column(file_name=file_name,
                      column_header="filt_width",
                      value=1)

    # load in arrays from .tsv file
    arrs = Arrays(file_name)

    # get strings for 3 bosons
    HName = masses.HName
    SName = masses.SName
    XName = masses.XName

    # get arrays of widths
    width_H = arrs.data('w_'+HName) / arrs.data('m'+HName)
    width_S = arrs.data('w_'+SName) / arrs.data('m'+SName)
    width_X = arrs.data('w_'+XName) / arrs.data('m'+XName)

    # get max_width from config file
    try:
        max_width_H: float = config_loader.get('width', 'max_width_H')
        max_width_S: float = config_loader.get('width', 'max_width_S')
        max_width_X: float = config_loader.get('width', 'max_width_X')
    except KeyError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

    # check whether each width is below the max width
    maskH = width_H < max_width_H
    maskS = width_S < max_width_S
    maskX = width_X < max_width_X

    # create the product of the 3 masks
    mask = maskH & maskS & maskX

    # create array of 0 and 1 based on mask
    filt_width = mask.astype(int)

    # overwrite filt_width array with new array
    arrs.set_array('filt_width',filt_width)

    # write new data to file
    arrs.write_file(file_name)

    # number of entries that pass
    npass = filt_width.sum()
    return npass
