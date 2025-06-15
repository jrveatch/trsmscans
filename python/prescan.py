#!/usr/bin/env python3

"""
Performs an initial scan ("prescan") over the scalar model parameter space.

This module generates a specified number of random scan points, evaluates them,
and writes the results to a `.tsv` file. Existing scan results can optionally be
extended or overwritten depending on user input.
"""

# TODO: Add prescan.log

# standard libraries
import argparse
import datetime
import logging
import os
import time
from typing import Union

# local modules
from utils.config_loader import ConfigLoader
from utils.file_utils import prescan_dir
from utils.logging_utils import LOG_LEVELS, setup_logging
from utils.model import Model
from utils.param_space import ParamSpace
from utils.parse import Parse
from utils.point_sampler import PointSampler
from utils.tsv_utils import count_tsv_points

# get logger
logger = logging.getLogger(__name__)

def prescan(model: Model,
            num_points: int,
            config_loader: Union[ConfigLoader, None] = None,
            config_file_name: Union[str, None] = None,
            overwrite: bool = False) -> Parse:
    """
    Executes a prescan of the parameter space for a given scalar model.

    If previous scan results exist, this function can either reuse, extend,
    or overwrite them based on user input and the `overwrite` flag.

    This method processes scan points in chunks (as defined by chunk_size)
    to allow for safe resumption and incremental progress tracking.

    Args:
        model (Model): The scalar model to scan.
        num_points (int): Total number of scan points to generate.
        config_loader (Union[ConfigLoader, None], optional): Optional configuration loader.
        config_file_name (Union[str, None], optional): Path to a config file if no loader is provided.
        overwrite (bool): If True, removes existing scan results before scanning.

    Returns:
        Parse: A Parse object that contains and can analyze the scan results.
    """

    # get scan start time
    scan_start = time.time()

    # directory where we want the output to go
    out_dir = prescan_dir(model)

    # names of .ini and .tsv files
    tsv_name = os.path.join(out_dir,f"{model.name}_prescan.tsv")

    # print starting message
    logger.info(f"Running a prescan with {num_points} points for {model.mass_string}")

    # get number of pre-existing prescan points
    num_existing = count_tsv_points(tsv_name)

    # if overwrite is set to True and requested points are < 20% of existing points, confirm with user
    if overwrite:
        if confirm_overwrite(existing=num_existing, requested=num_points):
            logger.info("Overwriting existing prescan")
            # remove existing TSV file and reset num_existing to 0
            if os.path.isfile(tsv_name):
                os.remove(tsv_name)
                num_existing = 0
        else:
            logger.info("Exiting prescan without changes")
            return Parse(model = model,
                         file_name = tsv_name)

    # calculate how many points we need to run
    num_points_to_run = compute_remaining_prescan_points(num_existing=num_existing,
                                                         requested=num_points)
    
    # return early if nothing more to run
    if num_points_to_run <= 0:
        return Parse(model = model,
                     file_name = tsv_name)

    # make output directory if it doesn't already exist
    os.makedirs(out_dir, exist_ok=True)

    # print location
    logger.debug(f"Running prescan in {out_dir}")

    # if config loader is not provided, create one
    if not config_loader:

        # use default config file name if none is provided
        if config_file_name is None:
            config_file_name = model.name + "_default.yml"

        logger.debug(f"Loading config file {config_file_name}")

        # load config file
        config_loader = ConfigLoader(config_file_name = config_file_name)

    # get configurations from config file
    try:
        chunk_size: int = config_loader.get('prescan', 'chunk_size')
    except Exception as e:
        logger.exception(e)
        raise

    # make sure chunk_size is a positive integer
    if chunk_size <= 0:
        raise ValueError("Chunk size must be a positive integer.")

    # make sure chunk_size is not larger than the number of points to run
    chunk_size = min(chunk_size, num_points_to_run)

    # make instance of param space with default model parameters
    param_space = ParamSpace(model)

    # create PointSampler object
    point_sampler = PointSampler(out_dir = out_dir,
                                 config_loader = config_loader)


    # run prescan in chunks until we reach the requested number of points
    parser = None
    while num_points_to_run > 0:
        num_current = count_tsv_points(tsv_name)
        remaining = num_points - num_current

        if remaining <= 0:
            logger.info(f"Reached {num_current} points, target met.")
            break

        this_batch = min(chunk_size, remaining)
        logger.info(f"Sampling {this_batch} points — progress: {num_current} / {num_points}")

        # Keep the parser from the latest run
        parser = point_sampler.sample_points(
            param_space = param_space,
            num_points_requested = this_batch,
            identifier = "prescan",
            good_points_only = False
        )

    # get total time taken
    scan_end = time.time()
    scan_time = (scan_end - scan_start)

    # print total time to the screen
    logger.info(f"Prescan took {datetime.timedelta(seconds=int(scan_time))} (hh:mm:ss)")

    # return parser after a successful run
    return parser or Parse(model=model, file_name=tsv_name)

def compute_remaining_prescan_points(num_existing: int,
                                     requested: int) -> int:
    """
    Computes how many additional prescan points need to be generated,
    given the number of existing points already written.

    Args:
        num_existing (int): The number of existing prescan points.
        requested (int): Number of scan points the user wants.

    Returns:
        int: Number of additional scan points to generate (could be zero).
    """

    if num_existing == 0:
        logger.info("No existing prescan points found, generating requested points")
        return requested

    if num_existing >= requested:
        logger.info(f"Found a prescan that already has {num_existing} points")
        logger.info(f"{requested} points requested, skipping since no more are needed")
        logger.info("If you want to overwrite the existing prescan, run with the -o option\n")
        return 0

    logger.info(f"{requested} prescan points requested and found existing prescan with {num_existing} points")
    logger.info(f"Running with the additional {requested - num_existing} points")
    logger.info("If you want to overwrite the existing prescan, run with the -o option\n")

    return requested - num_existing

def confirm_overwrite(existing: int,
                      requested: int) -> bool:
    """
    Prompts the user to confirm overwriting existing scan results if the requested
    number of scan points is significantly smaller than the existing number.

    Args:
        existing (int): The number of existing prescan points.
        requested (int): The number of new points requested by the user.

    Returns:
        bool: True if the overwrite is confirmed or not needed; False if the
        user declines to proceed with overwriting.
    """
    if requested < existing * 0.2:
        logger.info(f"{requested} points requested, but {existing} already exist.")
        while True:
            resp = input("Overwrite existing prescan? (yes/no): ").strip().lower()
            if resp in {"yes", "y"}:
                logger.info("User confirmed to overwrite existing prescan.")
                return True
            if resp in {"no", "n"}:
                logger.info("User declined to overwrite existing prescan.")
                return False
            print("Please enter 'yes' or 'no'.")
    return True

# Command-line interface for the prescan tool.
# Parses model parameters and scan settings from arguments, sets up logging,
# and executes a prescan over the parameter space.
if __name__ == "__main__":

    # parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-n", "--num_points", required=True, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    arg_parser.add_argument("--log-level", default="info", choices=LOG_LEVELS.keys(), help="Set the logging level")
    arg_parser.add_argument("-l", "--log", default="prescan.log", help="Log file name")
    args = arg_parser.parse_args()

    # create model object
    model = Model(name=args.model,
                  masses={'H': args.HMass, 'S': args.SMass, 'X': args.XMass})

    # directory where we want the output to go
    out_dir = prescan_dir(model)

    # set up logging
    setup_logging(log_file=os.path.join(out_dir, args.log),
                  level=LOG_LEVELS[args.log_level.lower()])

    prescan(model = model,
            num_points = args.num_points,
            overwrite = args.overwrite)
