#!/usr/bin/env python3

import argparse
import datetime
import os
import shutil
import time

from decimal import Decimal

import utils.decayutils as decayutils
import utils.fileutils as fileutils

from parse import Parse
from prescan import run_prescan
from utils.masses import Masses
from utils.params import Params
from utils.config_loader import ConfigLoader

from mean_shift_optimizer import MeanShiftOptimizer

class MeanShiftScanner:

    def __init__(self, args):
        self.__args = args

        self.__masses = Masses(mX=args.XMass, mS=args.SMass, mH=args.HMass)
        self.__global_params = Params(args.modelname, self.__masses)
        self.__scan_path = fileutils.scan_dir(args.modelname, args.decay, self.__masses)
        self.__plot_path = fileutils.plots_dir(args.modelname, args.decay, self.__masses)

        # use default config file name if none is provided
        if not config_file_name:
            config_file_name = args.modelname + "_default.yml"

        # load config file
        self.__config_loader = ConfigLoader(config_file_name=config_file_name)

        if not decayutils.is_valid_decay(args.decay):
            raise ValueError(f'Invalid decay mode: {args.decay}')

    def run(self):
        self.initialize_directories(self.__scan_path, self.__plot_path, self.__args, self.__masses, self.__global_params)

        self.prescan(self.__scan_path, self.__args, self.__masses, self.__global_params)

        os.chdir(self.__scan_path)

        self.scan(self.__scan_path, self.__plot_path, self.__args, self.__masses, self.__global_params)

    def scan(self):
        
        args = self.__args
        scan_path = self.__scan_path
        plot_path = self.__plot_path
        masses = self.__masses
        global_params = self.__global_params

        decay = args.decay
        model_name = self.__global_params.model_name()
        num_points = args.npoints
        use_multiprocessing = args.multiprocessing
        maxwidth = args.maxwidth

        stop_epochs: int = self.__config_loader.get('meanshift', 'stop_epochs')
        stop_mode: int = self.__config_loader.get('meanshift', 'stop_mode')
        stop_sens: float = self.__config_loader.get('meanshift', 'stop_sens')
        scan_volume: float = self.__config_loader.get('meanshift', 'scan_volume')

        summaryname = f"{scan_path}scansummary_{model_name}_{decay}_{masses}.txt"
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{masses}.txt"

        # get scan start time
        scanstart = time.time()

        label = f"MeanShifter"
        
        debug = False

        scanner = MeanShiftOptimizer(
            scan_path,
            plot_path,
            scan_volume,
            stop_mode,
            stop_epochs,
            stop_sens,
            label,
            num_points,
            decay,
            maxwidth,
            global_params,
            debug
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


    def prescan(self):

        args = self.__args
        scan_path = self.__scan_path
        masses = self.__masses
        global_params = self.__global_params

        decay = args.decay
        num_points = args.npoints
        model_name = global_params.model_name()
        max_width = args.maxwidth
        overwrite = args.overwrite
        n_prescan = min([num_points, 10000])
        use_multiprocessing = args.multiprocessing
        scan_path = fileutils.scan_dir(model_name, decay, masses)

        summaryname = f"{scan_path}scansummary_{model_name}_{decay}_{masses}.txt"
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{masses}.txt"

        # Call prescan and get result
        result = run_prescan(masses, model_name, num_points, max_width, overwrite, use_multiprocessing)

        # If prescan fails, remove directory and quit
        if result < 0:
            scan_path = fileutils.scan_dir(model_name, args.decay, masses)

            # Inform user
            print(f"Prescan failed, removing files dir {scan_path}")

            # Delete directory
            shutil.rmtree(scan_path)

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
        # NOTE: Presets scan range before meanshift..
        global_params.scale_ranges(opt_point)


    def initialize_directories(self):

        args = self.__args

        scan_path = self.__scan_path
        plot_path = self.__plot_path
        masses = self.__masses
        global_params = self.__global_params

        model_name = args.modelname
        decay = args.decay

        # Remove previous directories if overwrite == True
        if os.path.exists(scan_path) and args.overwrite:
            # remove directory
            shutil.rmtree(scan_path)
            
        if os.path.exists(plot_path):
            # remove directory
            shutil.rmtree(plot_path)

        # Create files directories
        if not os.path.exists(scan_path):
            os.makedirs(scan_path)
            os.makedirs(scan_path + "files")

        # Create summary file
        summaryname = f"{scan_path}scansummary_{model_name}_{decay}_{masses}.txt"
        summary = open(summaryname, "w")
        summary.write("Iter xbmax")
        for par in global_params.parameters().values():
            summary.write(" " + par.fullname())
        summary.write("\n")
        summary.close()

        # Create details file
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{masses}.txt"
        details = open(detailsname, "w")
        details.write("Scan details\n\n")
        details.close()