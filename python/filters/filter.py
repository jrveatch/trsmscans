#!/usr/bin/env python3

"""
Filter application script for scalar model scan results.

This script reads a `.tsv` file containing scan data, applies a series of
filters (width, bounds, and signal filters) based on a scalar model and
configuration, updates the `.tsv` file with filter results, and returns
filtering statistics.
"""

# standard libraries
import argparse
import logging
from typing import Dict

# local modules
from filters import bounds, width
from utils.df_utils import get_df, write_to_tsv
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

header_width = "filt_width"
header_bounds = "filt_bounds"
header_signals = "filt_signals"

def apply_filters(file_name: str,
                  model: Model,
                  use_multiprocessing: bool = True
                 ) -> Dict[str,int]:
    """
    Applies a set of filters to a scan result TSV file.

    This function loads scan results from a TSV file, applies width, bounds,
    and signal filters based on the given model and configuration, writes the
    updated results back to the file, and returns counts of how many entries
    pass each filter.

    Args:
        file_name (str): Path to the `.tsv` file containing scan results.
        model (Model): The scalar model defining relevant particle masses.

    Returns:
        Dict[str, int]: A dictionary with counts for each filter and the
        combined pass count. Keys include 'width', 'bounds', 'signals', and 'pass'.
    """

    # load in dataframe from .tsv file
    dataframe = get_df(file_name)

    # apply width filter
    width.filter_widths(dataframe=dataframe,
                        header_width=header_width,
                        model=model)

    # apply bounds and signals filters
    bounds.filter_bounds(dataframe=dataframe,
                         header_bounds=header_bounds,
                         header_signals=header_signals,
                         model=model,
                         use_multiprocessing=use_multiprocessing)

    # write updated dataframe to .tsv
    write_to_tsv(dataframe=dataframe,
                 file_name=file_name)

    # get results of each filter for counting
    filt_width = dataframe[header_width].astype(bool)
    filt_bounds = dataframe[header_bounds].astype(bool)
    filt_signals = dataframe[header_signals].astype(bool)

    # create dictionary to store results
    results: dict[str, int] = {}

    # find how many points pass all filters
    results["width"] = filt_width.sum()
    results["bounds"] = filt_bounds.sum()
    results["signals"] = filt_signals.sum()
    results["pass"] = (filt_width & filt_bounds & filt_signals).sum()

    # return numbers of events passing each filter
    return results

# Entry point for the script. Parses command-line arguments, constructs the model,
# loads configuration, and applies filters to the input TSV file.
if __name__ == "__main__":

    # parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-f", "--file_name", help="Name of file to apply filters to")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    apply_filters(file_name=args.file_name,
                  model=model)
