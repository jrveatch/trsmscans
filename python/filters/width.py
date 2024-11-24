#!/usr/bin/env python3

from utils.masses import Masses

from utils.config_loader import ConfigLoader

import pandas as pd

def filter_widths(dataframe: pd.DataFrame,
                  masses: Masses,
                  config_loader: 'ConfigLoader'
                 ) -> pd.Series:

    # get strings for 3 bosons
    HName = masses.HName
    SName = masses.SName
    XName = masses.XName

    # get arrays of widths
    width_H = dataframe['w_'+HName] / dataframe['m'+HName]
    width_S = dataframe['w_'+SName] / dataframe['m'+SName]
    width_X = dataframe['w_'+XName] / dataframe['m'+XName]

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

    return filt_width
