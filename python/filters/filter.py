#!/usr/bin/env python3

import argparse
import numpy as np

from filters import width
from filters import bounds
from utils import tsvutils
from utils.arrays import Arrays
from utils.masses import Masses
from utils.config_loader import ConfigLoader

header_width = "filt_width"
header_bounds = "filt_bounds"

def apply_filters(filename: str,
                  masses: Masses,
                  config_loader: 'ConfigLoader') -> tuple[int,int,int]:

    # initialize filter columns
    initialize_filters(filename)

    # get model name from config file
    try:
        modelname: float = config_loader.get('model', 'model_name')
    except KeyError as e:
        print(f"Error: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error: {e}")
        raise

    # apply width filter
    nwidth = width.filter_widths(filename=filename,
                                 config_loader=config_loader)

    # apply bounds filter
    nbounds = bounds.filter_bounds(filename=filename,
                                   modelname=modelname,
                                   masses=masses)

    # get arrays from output file
    arrays = Arrays(filename)

    # find how many points pass both filters
    filt_width = arrays.data(header_width)
    filt_bounds = arrays.data(header_bounds)
    filt_total = np.multiply(filt_width,filt_bounds)
    npass: int = filt_total.sum()

    # return numbers of events passing each filter
    return nwidth, nbounds, npass

def initialize_filters(filename: str) -> None:

    # initialize both columns
    tsvutils.initialize_column(filename=filename,
                               column_header=header_width,
                               value=1)
    tsvutils.initialize_column(filename=filename,
                               column_header=header_bounds,
                               value=1)

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-f", "--filename", help="Name of file to apply filters to")
    argparser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    args = argparser.parse_args()

    # create masses
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    apply_filters(filename=args.filename,masses=masses)
