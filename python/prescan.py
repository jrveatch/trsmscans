#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil
import time
import datetime
import argparse

# import package tools
from filters.filter import apply_filters, initialize_filters
from utils.runScannerS import runScannerS
from utils import tsvutils
from utils import fileutils
from utils.params import Params
from utils.masses import Masses
from parse import Parse
from utils.config_loader import ConfigLoader

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
    outdir = fileutils.prescan_dir(model_name=model_name,
                                   masses=masses)

    # names of .ini and .tsv files
    ini_name = outdir + model_name + ".ini"
    tsv_name_initial = outdir + model_name + ".tsv"
    tsv_name = outdir + model_name + "_prescan.tsv"

    # create parse object without .tsv file name
    parser = Parse(masses=masses,
                   model_name=model_name)

    # print starting message
    print("\nRunning a prescan with",num_points,"points for",str(masses))

    # get number of pre-existing prescan points
    num_existing = tsvutils.count_tsv_points(tsv_name)

    # if requested points are < 20% of existing points, request confirmation to overwrite
    if overwrite and num_points < num_existing * 0.2:
        print("You are requesting",num_points,"points but there are already",num_existing,"points")
        while True:
            # get user response
            response = input("Are you sure you want to overwrite the existing prescan? (yes/no): ").strip().lower()
            # if yes, print message and break out of while loop
            if response in ["yes", "y"]:
                print("Overwriting existing prescan")
                break
            # if no, print message and return
            elif response in ["no", "n"]:
                parser.read_file(tsv_name)
                print("Exiting prescan")
                return parser
            # complain if response is neither yes nor no
            else:
                print("Please enter 'yes' or 'no'.")

    # remove previous directory if set to overwrite
    if os.path.exists(outdir) and overwrite:
        # remove directory
        shutil.rmtree(outdir)
        # reset num_existing to 0
        num_existing = 0

    # if prescan exists, adjust the number of prescan points to run
    if num_existing > 0:

        # if enough points already exist, parse and return
        if num_existing >= num_points:
            print("Found a prescan that already has",num_existing,"points.")
            print(num_points,"points request, skipping since no more are needed.")
            print("If you want to overwrite the existing prescan, run with the -o option.")
            parser.read_file(tsv_name)
            return parser

        # otherwise reduce the number of points to run with
        num_points_old = num_points
        num_points -= num_existing
        print("Found prescan with",num_existing,"points.")
        print(num_points_old,"prescan points requested, so I am running with",num_points,"points.")
        print("If you want to overwrite the existing prescan, run with the -o option.")

    # check if directory exists, if not make it
    if not os.path.exists(outdir):
        os.makedirs(outdir)

    # store starting directory
    startDir = os.getcwd()

    # move into working directory for prescan
    os.chdir(outdir)

    # print location
    print("Running prescan in",outdir)

    # if config loader is not provided, create one
    if not config_loader:

        # use default config file name if none is provided
        if not config_file_name:
            config_file_name = model_name + "_default.yml"

        # load config file
        config_loader = ConfigLoader(config_file_name=config_file_name)

    # make instance of params
    # this automatically initializes the parameters
    params = Params(model_name,masses)

    # write .ini file from template
    params.write_ini(ini_name)

    # run ScannerS to sample points
    try:
        runScannerS(ini_name = ini_name,
                    model_name = model_name,
                    num_points = num_points,
                    use_multiprocessing = use_multiprocessing)

    # if timeout error is caught, delete the directory and raise
    except TimeoutError:

        # delete directory
        shutil.rmtree(outdir)

        # return result from process
        raise

    # make sure new .tsv has filter columns
    initialize_filters(file_name=tsv_name_initial)

    # save output to tsv_name
    tsvutils.save_tsv_output(input_file = tsv_name_initial,
                             output_file = tsv_name)

    # apply width and bounds filters
    apply_filters(file_name = tsv_name,
                  masses = masses,
                  config_loader = config_loader)

    # parse output .tsv file
    parser.read_file(tsv_name)

    # get total time taken
    scan_end = time.time()
    scan_time = (scan_end - scan_start)

    # move back to the starting directory
    os.chdir(startDir)

    # print total time to the screen
    print("Prescan took",str(datetime.timedelta(seconds=int(scan_time))),"(hh:mm:ss)")

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
    args = arg_parser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass,mS=args.SMass,mH=args.HMass)

    run_prescan(masses = masses,
                model_name = args.model,
                num_points = args.npoints,
                overwrite = args.overwrite,
                use_multiprocessing = args.multiprocessing)
