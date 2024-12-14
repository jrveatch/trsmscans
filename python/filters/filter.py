#!/usr/bin/env python3

# standard libraries
import argparse
import logging

# local modules
from filters import bounds, width
from utils.config_loader import ConfigLoader
from utils.df_utils import get_df, write_to_tsv
from utils.masses import Masses

# get logger
logger = logging.getLogger(__name__)

header_width = "filt_width"
header_bounds = "filt_bounds"
header_signals = "filt_signals"

def apply_filters(file_name: str,
                  masses: Masses,
                  config_loader: 'ConfigLoader'
                 ) -> tuple[int,int,int]:

    # load in dataframe from .tsv file
    dataframe = get_df(file_name)

    # get model name from config file
    try:
        model_name: float = config_loader.get('model', 'model_name')
    except KeyError as e:
        logger.error(e)
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise

    # apply width filter
    width.filter_widths(dataframe=dataframe,
                        header_width=header_width,
                        masses=masses,
                        config_loader=config_loader)

    # apply bounds and signals filters
    bounds.filter_bounds(dataframe=dataframe,
                         header_bounds=header_bounds,
                         header_signals=header_signals,
                         model_name=model_name,
                         masses=masses)

    # write updated dataframe to .tsv
    write_to_tsv(dataframe=dataframe,
                 file_name=file_name)

    # get results of each filter for counting
    filt_width = dataframe[header_width]
    filt_bounds = dataframe[header_bounds]
    filt_signals = dataframe[header_signals]

    # find how many points pass all filters
    nwidth: int = filt_width.sum()
    nbounds: int = filt_bounds.sum()
    nsignals: int = filt_signals.sum()
    npass: int = (filt_width * filt_bounds * filt_signals).sum()

    # return numbers of events passing each filter
    return nwidth, nbounds, nsignals, npass

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
