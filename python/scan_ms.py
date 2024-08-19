#!/usr/bin/env python3

import argparse
import datetime
import os
import shutil
import time

from decimal import Decimal
from typing import cast

import utils.decayutils as decayutils
import utils.fileutils as fileutils

from parse import Parse
from prescan import run_prescan
from utils.masses import Masses
from utils.params import Params
from utils.mean_shifter import MeanShifter

def main(args):
    model_name = args.modelname
    decay = args.decay

    masses = Masses(mX=args.XMass, mS=args.SMass, mH=args.HMass)
    global_params = Params(model_name, masses)
    files_path = fileutils.scan_dir(model_name, decay, masses)

    if not decayutils.isValidDecay(decay):
        raise ValueError(f'Invalid decay mode: {decay}')

    initialize_directories(files_path, args, masses, global_params)

    prescan(files_path, masses, global_params, args)

    os.chdir(files_path)

    scan_op(files_path, args, masses, global_params)


def scan_op(files_path: str, args: argparse.Namespace, masses: Masses, global_params: Params):

    decay = args.decay
    model_name = global_params.model_name()
    num_scanners = args.numscanners
    num_points = args.npoints
    scan_prop = args.scanprop
    use_multiprocessing = args.multiprocessing
    maxwidth = args.maxwidth
    stop_sens = args.stopsens
    stop_epochs = args.stopepochs

    summaryname = f"{files_path}scansummary_{model_name}_{decay}_{masses}.txt"
    detailsname = f"{files_path}scandetails_{model_name}_{decay}_{masses}.txt"

    # get scan start time
    scanstart = time.time()

    for i in range(num_scanners):
        label = f"MeanShifter-{i}"
        
        scanner = MeanShifter(
            files_path,
            scan_prop,
            stop_epochs,
            stop_sens,
            label,
            num_points,
            decay,
            maxwidth,
            global_params,
            True
        )

        opt = scanner.run(use_multiprocessing)

        # Write to summary file
        with open(summaryname, 'a') as file:
            file.write(f"Opt {' '.join([str(e) for e in opt])}")

    # SCAN LOGIC END HERE

    # get total scan time
    scanend = time.time()
    scantime = (scanend - scanstart)

    # print out scan time
    print("\nDone!")
    print("Scan took", str(datetime.timedelta(seconds=int(scantime))), "(hh:mm:ss)\n")

    # write time info to details file
    details = open(detailsname, "a")
    details.write("Scan took " + str(datetime.timedelta(seconds=int(scantime))) + " (hh:mm:ss)")
    details.close()
    return


def prescan(files_path: str, masses: Masses, global_params: Params, args: argparse.Namespace):

    decay = args.decay
    num_points = args.npoints
    model_name = global_params.model_name()
    max_width = args.maxwidth
    overwrite = args.overwrite
    n_prescan = min([num_points, 10000])
    use_multiprocessing = args.multiprocessing
    files_path = fileutils.scan_dir(model_name, decay, masses)

    summaryname = f"{files_path}scansummary_{model_name}_{decay}_{masses}.txt"
    detailsname = f"{files_path}scandetails_{model_name}_{decay}_{masses}.txt"

    # Call prescan and get result
    result = run_prescan(masses, model_name, num_points, max_width, overwrite, use_multiprocessing)

    # If prescan fails, remove directory and quit
    if result < 0:
        files_path = fileutils.scan_dir(model_name, args.decay, masses)

        # Inform user
        print(f"Prescan failed, removing files dir {files_path}")

        # Delete directory
        shutil.rmtree(files_path)

        raise (RuntimeError("Prescan failure, see output"))

    prescan_tsv_path = fileutils.prescan_tsv(model_name, masses)

    parser = Parse(masses, decay, model_name, prescan_tsv_path)

    # get the number of unfiltered prescan points available
    n_prescan_unfiltered = parser.get_n_unfiltered_points()

    # get the number of filtered prescan points available
    n_prescan = parser.get_n_points()

    # info message about prescan
    print("\nAnalyzing prescan with", n_prescan_unfiltered, "points")
    print(n_prescan, "points passed filters")

    # if the prescan ranges are more than 1% of the max range
    # away from the boundaries, change the boundaries to restrict
    # scan range and minimize scan points that are wasted

    # print header about prescan ranges to the screen
    print("Found the following ranges from the prescan:")

    # loop over parameters
    for par in global_params.parnames():

        # getting 1% of min and max from the model
        one_percent = (global_params.starting_max(par) - global_params.starting_min(par)) / 100

        # get min and max from prescan
        newMin = parser.get_min(par)
        newMax = parser.get_max(par)

        # check min value
        if newMin - one_percent > global_params.lower_bound(par):
            global_params.set_lower_bound(par, newMin - one_percent)

        # check max value
        if newMax + one_percent < global_params.upper_bound(par):
            global_params.set_upper_bound(par, newMax + one_percent)

        # print min and max to screen after prescan
        global_params.print_bounds(par)

    # get scan density
    density = n_prescan / global_params.volume()

    # get new points
    opt_point = parser.get_max_xb_point()

    # write scan details to details file
    details = open(detailsname, "a")
    details.write("Prescan\n")
    details.write("--------------------\n")
    details.write("Number of prescan points = " + str(n_prescan) + "\n")
    details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
    details.write("Max xsec*BR = " + opt_point.format_xb() + "\n")
    details.write("--------------------\n")
    for par in global_params.parnames():
        details.write(par + ":\n")
        details.write("  " + opt_point.format_param(par) + "\n")
        details.write("  " + global_params.parameter(par).format_range() + "\n")
    details.write("--------------------\n")
    details.write("\n\n")
    details.close()

    # write scan results to summary file
    summary = open(summaryname, "a")
    summary.write("Pre")
    summary.write(" " + opt_point.format_xb())
    for name, par in global_params.parameters().items():
        summary.write(" " + f"{opt_point.get_val(name):1.{par.precision()}f}")
    summary.write("\n")
    summary.close()

    # scale new low and high values
    global_params.scale_ranges(opt_point)


def initialize_directories(path: str, args: argparse.Namespace, masses: Masses, params: Params):
    model_name = args.modelname
    decay = args.decay

    # Remove previous directories if overwrite == True
    if os.path.exists(path) and args.overwrite:
        # remove directory
        shutil.rmtree(path)

    # Create files directories
    if not os.path.exists(path):
        os.makedirs(path)
        os.makedirs(path + "files")

    # Create summary file
    summaryname = f"{path}scansummary_{model_name}_{decay}_{masses}.txt"
    summary = open(summaryname, "w")
    summary.write("Iter xbmax")
    for par in params.parameters().values():
        summary.write(" " + par.fullname())
    summary.write("\n")
    summary.close()

    # Create details file
    detailsname = f"{path}scandetails_{model_name}_{decay}_{masses}.txt"
    details = open(detailsname, "w")
    details.write("Scan details\n\n")
    details.close()


if __name__ == "__main__":

    # Parse command line arguments
    argparser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    argparser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    argparser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    argparser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    argparser.add_argument("-M", "--modelname", required=True, type=str, help="Model name")
    argparser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    argparser.add_argument("-n", "--npoints", required=True, type=int, help="Initial number of scan points")

    argparser.add_argument("-ns", "--numscanners", default=1, type=int, help="Number of scanners to use")
    argparser.add_argument("-sp", "--scanprop", default=0.1, type=float, help="Proportion of total volume to use for scan volume")
    argparser.add_argument("-ss", "--stopsens", default=0.1, type=float, help="Scan sensitivity for stopping conditions")
    argparser.add_argument("-se", "--stopepochs", default=3, type=int, help="Scan epochs used for stopping conditions")

    argparser.add_argument("-w", "--maxwidth", default=0.15, type=float, help="Maximum allowed width for any scalar")
    argparser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    argparser.add_argument("-o", "--overwrite", action="store_true", help="Whether overwrite should be used")

    main(argparser.parse_args())
