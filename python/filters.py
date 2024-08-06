#!/usr/bin/env python3

import argparse
import numpy as np

from typing import Tuple

from utils import width
from utils import bounds
from utils import tsvutils
from utils.arrays import Arrays
from utils.masses import Masses

header_width = "filt_width"
header_bounds = "filt_bounds"

def apply_filters(filename: str,
                  modelname: str,
                  masses: Masses,
                  maxwidth: float) -> Tuple[int,int,int]:

    # initialize filter columns
    initialize_filters(filename)

    # apply width filter
    nwidth = width.filter_widths(filename=filename,
                                 maxwidth=maxwidth)

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
    tsvutils.initializeColumn(filename=filename,
                              column_header=header_width,
                              value=1)
    tsvutils.initializeColumn(filename=filename,
                              column_header=header_bounds,
                              value=1)

if __name__ == "__main__":

    # parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-f", "--filename", help="Name of file to apply filters to")
    argparser.add_argument("-w", "--maxwidth", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    args = argparser.parse_args()

    # create masses
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    applyFilters(filename=args.filename,maxwidth=args.maxwidth,masses=masses)
