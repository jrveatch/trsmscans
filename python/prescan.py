#!/usr/bin/env python3

# standard libraries
import argparse
import datetime
import logging
import os
import shutil
import time

# local modules
from point_sampler import PointSampler
from utils.config_loader import ConfigLoader
from utils.file_utils import prescan_dir
from utils.logging_utils import LOG_LEVELS, setup_logging
from utils.masses import Masses
from utils.params import Params
from utils.parse import Parse
from utils.tsv_utils import count_tsv_points

# get logger
logger = logging.getLogger(__name__)

def run_prescan(masses: 'Masses',
                model_name: str,
                num_points: int,
                config_loader: ConfigLoader | None = None,
                config_file_name: str = "",
                overwrite: bool = False,
                use_multiprocessing: bool = False) -> 'Parse':

    # get scan start time
    scan_start = time.time()

    # directory where we want the output to go
    out_dir = prescan_dir(model_name = model_name,
                          masses = masses)

    # names of .ini and .tsv files
    tsv_name = out_dir + model_name + "_prescan.tsv"

    # print starting message
    logger.info(f"Running a prescan with {num_points} points for {str(masses)}")

    # get number of pre-existing prescan points
    num_existing = count_tsv_points(tsv_name)

    # if requested points are < 20% of existing points, request confirmation to overwrite
    if overwrite and num_points < num_existing * 0.2:
        logger.info(f"You are requesting {num_points} points but there are already {num_existing} points")
        while True:
            # get user response
            response = input("Are you sure you want to overwrite the existing prescan? (yes/no): ").strip().lower()
            # if yes, print message and break out of while loop
            if response in ["yes", "y"]:
                logger.info("Overwriting existing prescan")
                break
            # if no, print message and return
            elif response in ["no", "n"]:
                logger.info("Exiting prescan")
                return Parse(masses = masses,
                             model_name = model_name,
                             file_name = tsv_name)
            # complain if response is neither yes nor no
            else:
                logger.warning("Please enter 'yes' or 'no'.")

    # remove previous directory if set to overwrite
    if os.path.exists(out_dir) and overwrite:
        # remove directory
        shutil.rmtree(out_dir)
        # reset num_existing to 0
        num_existing = 0

    # if prescan exists, adjust the number of prescan points to run
    if num_existing > 0:

        # if enough points already exist, parse and return
        if num_existing >= num_points:
            logger.info(f"Found a prescan that already has {num_existing} points")
            logger.info(f"{num_points} points requested, skipping since no more are needed")
            logger.info("If you want to overwrite the existing prescan, run with the -o option")
            return Parse(masses = masses,
                         model_name = model_name,
                         file_name = tsv_name)

        # otherwise reduce the number of points to run with
        num_points_old = num_points
        num_points -= num_existing
        logger.info(f"{num_points_old} prescan points requested and found existing prescan with {num_existing} points")
        logger.info(f"Running with the additional {num_points} points")
        logger.info("If you want to overwrite the existing prescan, run with the -o option")

    # check if directory exists, if not make it
    if not os.path.exists(out_dir):
        os.makedirs(out_dir)

    # store starting directory
    startDir = os.getcwd()

    # move into working directory for prescan
    os.chdir(out_dir)

    # print location
    logger.debug(f"Running prescan in {out_dir}")

    # if config loader is not provided, create one
    if not config_loader:

        # use default config file name if none is provided
        if not config_file_name:
            config_file_name = model_name + "_default.yml"

        # load config file
        config_loader = ConfigLoader(config_file_name = config_file_name)

    # make instance of params
    # this automatically initializes the parameters
    params = Params(model_name,masses)

    # create PointSampler object
    point_sampler = PointSampler(out_dir = out_dir,
                                 model_name = model_name,
                                 use_multiprocessing = use_multiprocessing,
                                 config_loader = config_loader)

    # sample points
    parser = point_sampler.sample_points(params = params,
                                         identifier = "prescan",
                                         npoints = num_points,
                                         good_points_only = False)

    # get total time taken
    scan_end = time.time()
    scan_time = (scan_end - scan_start)

    # move back to the starting directory
    os.chdir(startDir)

    # print total time to the screen
    logger.info(f"Prescan took {str(datetime.timedelta(seconds=int(scan_time)))} (hh:mm:ss)")

    # return parser after a successful run
    return parser

if __name__ == "__main__":

    # parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous prescan")
    arg_parser.add_argument("-m", "--multiprocessing", action="store_true", help="Use if multiprocessing should be used")
    arg_parser.add_argument("--log-level", default="info", choices=LOG_LEVELS.keys(), help="Set the logging level (default: info)")
    args = arg_parser.parse_args()

    # set up logging
    setup_logging(level=LOG_LEVELS[args.log_level.lower()])

    # create masses object
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    run_prescan(masses = masses,
                model_name = args.model,
                num_points = args.npoints,
                overwrite = args.overwrite,
                use_multiprocessing = args.multiprocessing)
