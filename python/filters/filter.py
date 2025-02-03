#!/usr/bin/env python3

# standard libraries
import argparse
import logging

# local modules
from filters import bounds, width
from utils.config_loader import ConfigLoader
from utils.df_utils import get_df, write_to_tsv
from utils.model import Model

# get logger
logger = logging.getLogger(__name__)

header_width = "filt_width"
header_bounds = "filt_bounds"
header_signals = "filt_signals"

def apply_filters(file_name: str,
                  model: 'Model',
                  config_loader: 'ConfigLoader'
                 ) -> tuple[int,int,int]:

    # load in dataframe from .tsv file
    dataframe = get_df(file_name)

    # apply width filter
    width.filter_widths(dataframe=dataframe,
                        header_width=header_width,
                        model=model,
                        config_loader=config_loader)

    # apply bounds and signals filters
    bounds.filter_bounds(dataframe=dataframe,
                         header_bounds=header_bounds,
                         header_signals=header_signals,
                         model=model)

    # write updated dataframe to .tsv
    write_to_tsv(dataframe=dataframe,
                 file_name=file_name)

    # get results of each filter for counting
    filt_width = dataframe[header_width]
    filt_bounds = dataframe[header_bounds]
    filt_signals = dataframe[header_signals]

    # create dictionary to store results
    results: dict[str, int] = {}

    # find how many points pass all filters
    results["width"] = filt_width.sum()
    results["bounds"] = filt_bounds.sum()
    results["signals"] = filt_signals.sum()
    results["pass"] = (filt_width * filt_bounds * filt_signals).sum()

    # return numbers of events passing each filter
    return results

if __name__ == "__main__":

    # parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-f", "--file_name", help="Name of file to apply filters to")
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    apply_filters(file_name=args.file_name,model=model)
