#!/usr/bin/env python3

import argparse
import numpy as np

from filters import width
from filters import bounds
from utils.tsv_utils import initialize_column
from utils.arrays import Arrays
from utils.masses import Masses
from utils.config_loader import ConfigLoader

header_width = "filt_width"
header_bounds = "filt_bounds"
header_signals = "filt_signals"

def apply_filters(file_name: str,
                  masses: Masses,
                  config_loader: 'ConfigLoader') -> tuple[int,int,int]:

    # initialize filter columns
    initialize_filters(file_name)

    # get model name from config file
    try:
        model_name: float = config_loader.get('model', 'model_name')
    except KeyError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

    # apply width filter
    nwidth = width.filter_widths(file_name=file_name,
                                 masses=masses,
                                 config_loader=config_loader)

    # apply bounds filter
    nbounds, nsignals = bounds.filter_bounds(file_name=file_name,
                                             model_name=model_name,
                                             masses=masses)

    # get arrays from output file
    arrays = Arrays(file_name)

    # find how many points pass both filters
    filt_width = arrays.data(header_width)
    filt_bounds = arrays.data(header_bounds)
    filt_signals = arrays.data(header_signals)
    filt_total = np.multiply(filt_width,filt_bounds,filt_signals)
    npass: int = filt_total.sum()

    # return numbers of events passing each filter
    return nwidth, nbounds, nsignals, npass

def initialize_filters(file_name: str) -> None:

    # initialize all columns
    initialize_column(file_name=file_name,
                      column_header=header_width,
                      value=1)
    initialize_column(file_name=file_name,
                      column_header=header_bounds,
                      value=1)
    initialize_column(file_name=file_name,
                      column_header=header_signals,
                      value=1)

if __name__ == "__main__":

    # parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-f", "--file_name", help="Name of file to apply filters to")
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    args = arg_parser.parse_args()

    # create masses
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    apply_filters(file_name=args.file_name,masses=masses)
