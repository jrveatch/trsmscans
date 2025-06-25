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
from filters.bounds import BoundsFilter
from filters.width import WidthFilter
from utils.df_utils import get_df, write_to_tsv
from utils.model import Model

class FilterPipeline:
    """
    Coordinates application of width, bounds, and signal filters to scalar model scan data.

    This pipeline loads scan results from a TSV file, applies a width-based filter
    using a configuration-defined threshold, and evaluates HiggsBounds and HiggsSignals
    criteria using external tools. Results are written back to the file, and basic
    filtering statistics are returned.
    """

    header_width = "filt_width"
    header_bounds = "filt_bounds"
    header_signals = "filt_signals"

    def __init__(self,
                 model: Model):
        """
        Initializes the filtering pipeline with the given scalar model.

        Args:
            model (Model): The scalar model providing scalar names and config context.
        """
        self.width_filter = WidthFilter(model)
        self.bounds_filter = BoundsFilter(model)

    def apply_filters(self,
                      file_name: str,
                      use_multiprocessing: bool = True) -> Dict[str, int]:
        """
        Applies width, bounds, and signal filters to a scan result file.

        Reads a TSV file into a DataFrame, applies filters in sequence,
        writes updated results back to disk, and returns filter pass counts.

        Args:
            file_name (str): Path to the `.tsv` file containing scan results.
            use_multiprocessing (bool): Whether to enable parallel processing for bounds filtering.

        Returns:
            Dict[str, int]: A dictionary with counts of rows passing each individual filter
                            and all filters combined. Keys include 'width', 'bounds', 'signals', and 'pass'.
        """

        dataframe = get_df(file_name)

        # Apply filters
        self.width_filter.apply(dataframe=dataframe,
                                header=self.header_width)
        self.bounds_filter.apply(dataframe=dataframe,
                                 header_bounds=self.header_bounds,
                                 header_signals=self.header_signals,
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
