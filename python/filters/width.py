#!/usr/bin/env python3

"""
Applies width-based filtering to scalar particles in a model scan.

This module defines a filter that flags parameter points where the particle widths
are within an allowed fraction of their corresponding masses. The width thresholds
are read from a configuration file.
"""

# standard libraries
import logging

# third-party libraries
import numpy as np
import pandas as pd

# local modules
from utils.config_loader import ConfigLoader
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

def filter_widths(dataframe: pd.DataFrame,
                  header_width: str,
                  model: Model,
                  config_loader: ConfigLoader
                 ) -> None:
    """
    Adds a binary filter column to the DataFrame indicating whether all scalar
    widths are below their allowed thresholds.

    Thresholds are defined as a fraction of the mass for each scalar particle
    and are configured externally via the ConfigLoader.

    Args:
        dataframe (pd.DataFrame): The scan data containing width and mass columns.
        header_width (str): The name of the column to add (e.g., 'filt_width').
        model (Model): Model object providing scalar name mappings.
        config_loader (ConfigLoader): Loader object for reading threshold values.

    Raises:
        KeyError: If any required configuration keys are missing.
        Exception: For any unexpected errors during processing.
    """

    # get strings for 3 bosons
    HName = model.get_ordered_scalar_name('H')
    SName = model.get_ordered_scalar_name('S')
    XName = model.get_ordered_scalar_name('X')

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
