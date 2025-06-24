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
from typing import Dict

# local modules
from filters import bounds
from filters.width import WidthFilter
from utils.df_utils import get_df, write_to_tsv
from utils.model import Model

class FilterPipeline:
    header_width = "filt_width"
    header_bounds = "filt_bounds"
    header_signals = "filt_signals"

    def __init__(self,
                 model: Model):
        self.model = model # TODO: remove this when it is no longer needed
        self.width_filter = WidthFilter(model)

    def apply_filters(self,
                      file_name: str,
                      use_multiprocessing: bool = True) -> Dict[str, int]:

        dataframe = get_df(file_name)

        # Apply filters
        self.width_filter.apply(dataframe=dataframe,
                                header=self.header_width)

        # apply bounds and signals filters
        bounds.filter_bounds(dataframe=dataframe,
                            header_bounds=self.header_bounds,
                            header_signals=self.header_signals,
                            model=self.model,
                            use_multiprocessing=use_multiprocessing)

        # Write updated dataframe
        write_to_tsv(dataframe, file_name)

        # Compute stats
        f_width = dataframe[self.header_width].astype(bool)
        f_bounds = dataframe[self.header_bounds].astype(bool)
        f_signals = dataframe[self.header_signals].astype(bool)

        return {
            "width": f_width.sum(),
            "bounds": f_bounds.sum(),
            "signals": f_signals.sum(),
            "pass": (f_width & f_bounds & f_signals).sum(),
        }

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

    filter_pipeline = FilterPipeline(model)

    filter_pipeline.apply_filters(file_name=args.file_name)
