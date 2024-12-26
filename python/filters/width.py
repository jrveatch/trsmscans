#!/usr/bin/env python3

# standard libraries
import logging

# third-party libraries
import numpy as np
import pandas as pd

# local modules
from utils.config_loader import ConfigLoader
from utils.masses import Masses

# get logger
logger = logging.getLogger(__name__)

def filter_widths(dataframe: pd.DataFrame,
                  header_width: str,
                  masses: Masses,
                  config_loader: 'ConfigLoader'
                 ) -> None:

    # get strings for 3 bosons
    HName = masses.HName
    SName = masses.SName
    XName = masses.XName

    # get max_width from config file
    try:
        max_width_H: float = config_loader.get('width', 'max_width_H')
        max_width_S: float = config_loader.get('width', 'max_width_S')
        max_width_X: float = config_loader.get('width', 'max_width_X')
    except KeyError as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

    # get arrays of widths, masses and thresholds
    arr_widths = dataframe[['w_' + HName, 'w_' + SName, 'w_' + XName]].to_numpy()
    arr_masses = dataframe[['m' + HName, 'm' + SName, 'm' + XName]].to_numpy()
    arr_thresholds = np.array([max_width_H, max_width_S, max_width_X])

    # create filter as a mask that checks each width is below the max width
    filt_width = np.all(arr_widths < arr_masses * arr_thresholds, axis=1)

    # add filter to dataframe
    dataframe[header_width] = filt_width.astype(int)

    return
