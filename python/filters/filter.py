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
from typing import Dict, Tuple

import pandas as pd

# local modules
from filters.bounds import BoundsFilter
from filters.width import WidthFilter
from utils.config_loader import ConfigLoader
from utils.df_utils import get_df
from utils.model import Model

# get logger
import logging
logger = logging.getLogger(__name__)

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
        try:
            run_config = ConfigLoader("RunConfig.yml")
            min_chunk_size: int = run_config.get("bounds", "min_chunk_size")
        except Exception:
            logger.exception("Failed to load bounds filtering configuration.")
            raise
        self.width_filter = WidthFilter(model)
        self.bounds_filter = BoundsFilter(model, min_chunk_size)

    def apply_filters(self,
                      data: pd.DataFrame,
                      use_multiprocessing: bool = True,
                     ) -> Tuple[pd.DataFrame, Dict[str, int]]:
        """
        Evaluate all configured filters for the provided scan points.

        The width, HiggsBounds, and HiggsSignals filters are applied and their
        results are appended as new columns using a single concatenation operation.

        Args:
            data (pd.DataFrame): Scan points to evaluate.
            use_multiprocessing (bool): Whether to use multiprocessing when
                evaluating HiggsBounds and HiggsSignals.

        Returns:
            Tuple[pd.DataFrame, Dict[str, int]]:
                The filtered DataFrame and a summary of filter pass counts.
        """
        width_result = self.width_filter.apply(
            data = data,
            header = self.header_width
        )

        bounds_results = self.bounds_filter.apply(
            data = data,
            header_bounds = self.header_bounds,
            header_signals = self.header_signals,
            use_multiprocessing = use_multiprocessing
        )

        data = pd.concat(
            [
                data,
                width_result,
                bounds_results,
            ],
            axis=1,
        )

        f_width = data[self.header_width].astype(bool)
        f_bounds = data[self.header_bounds].astype(bool)
        f_signals = data[self.header_signals].astype(bool)

        results = {
            "width": int(f_width.sum()),
            "bounds": int(f_bounds.sum()),
            "signals": int(f_signals.sum()),
            "pass": int((f_width & f_bounds & f_signals).sum()),
        }

        return data, results

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

    data = get_df(args.file_name)

    data, results = filter_pipeline.apply_filters(data=data)
