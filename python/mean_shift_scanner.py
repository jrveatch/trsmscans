#!/usr/bin/env python3

import datetime
import os
import random
import shutil
import time

from copy import deepcopy
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

        masses = Masses(mX=args.XMass, mS=args.SMass, mH=args.HMass)
        self.__global_params = Params(args.model, masses)
        self.__scan_path = fileutils.scan_dir(args.model, args.decay, masses)
        self.__plot_path = fileutils.plots_dir(args.model, args.decay, masses)

        # use default config file name if none is provided
        config_file_name = args.model + "_default.yml"

        # load config file
        self.__config_loader = ConfigLoader(config_file_name=config_file_name)

        if not decayutils.is_valid_decay(args.decay):
            raise ValueError(f'Invalid decay mode: {args.decay}')

    def run(self):
        self.initialize_directories()

        self.prescan()

        os.chdir(self.__scan_path)

        self.scan()

    def scan(self):
        
        args = self.__args
        config_loader = self.__config_loader
        scan_path = self.__scan_path
        plot_path = self.__plot_path
        global_params = self.__global_params

        decay = args.decay
        model_name = self.__global_params.model_name()
        num_points = args.npoints
        use_multiprocessing = args.multiprocessing

        stop_epochs: int = self.__config_loader.get('meanshift', 'stop_epochs')
        stop_mode: int = self.__config_loader.get('meanshift', 'stop_mode')
        stop_sens: float = self.__config_loader.get('meanshift', 'stop_sens')
        scan_volume: float = self.__config_loader.get('meanshift', 'scan_volume')
        points_num: int = self.__config_loader.get('meanshift', 'points_num')
        points_gen: str = self.__config_loader.get('meanshift', 'points_gen')
        debug: bool = self.__config_loader.get('meanshift', 'debug')

        summaryname = f"{scan_path}scansummary_{model_name}_{decay}_{global_params.masses()}.txt"
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{global_params.masses()}.txt"

        # get scan start time
        scanstart = time.time()

        initial_pos_set = self.__get_initial_positions(points_num, points_gen)

        print("\nInitial points:")
        for p in initial_pos_set:
            print(f"\t{p}")

        for i, initial_pos in enumerate(initial_pos_set):
            label = f"MeanShiftOptimizer-{i}"

            opt = MeanShiftOptimizer(
                scan_path=scan_path,
                plot_path=plot_path,
                scan_volume=scan_volume,
                stop_mode=stop_mode,
                stop_epochs=stop_epochs,
                stop_sens=stop_sens,
                label=label,
                initial_pos=initial_pos,
                num_points=num_points,
                decay=decay,
                global_params=global_params,
                config_loader=config_loader,
                debug=debug
            ).run(use_multiprocessing)

            with open(summaryname, 'a') as scan_summary:
                scan_summary.write(f"Ini_{i} {' '.join([str(e) for e in initial_pos])}\n")
                scan_summary.write(f"Opt_{i} {' '.join([str(e) for e in opt])}\n")

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
        global_params = self.__global_params
        masses = global_params.masses()

        decay = args.decay
        num_points = args.npoints
        model_name = global_params.model_name()
        overwrite = args.overwrite
        n_prescan = min([num_points, 10000])
        use_multiprocessing = args.multiprocessing
        scan_path = fileutils.scan_dir(model_name, decay, masses)

        summaryname = f"{scan_path}scansummary_{model_name}_{decay}_{masses}.txt"
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{masses}.txt"

        # Call prescan and get result
        result = run_prescan(
            masses=masses,
            model_name=model_name,
            num_points=num_points,
            config_loader=self.__config_loader, 
            overwrite=overwrite, 
            use_multiprocessing=use_multiprocessing)

        # If prescan fails, remove directory and quit
        if result is None:
            scan_path = fileutils.scan_dir(model_name, args.decay, masses)

            # Inform user
            print(f"Prescan failed, removing files dir {scan_path}")

            # Delete directory
            shutil.rmtree(scan_path)

            raise (RuntimeError("Prescan failure, see output"))

        prescan_tsv_path = fileutils.prescan_tsv(model_name, masses)

        parser = Parse(
            masses=masses,
            model_name=model_name,
            file_name=prescan_tsv_path)

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
        for name in global_params.parameter_names():

            # getting 1% of min and max from the model
            one_percent = (global_params.starting_max(name) - global_params.starting_min(name)) / 100

            # get min and max from prescan
            newMin = parser.get_min(name)
            newMax = parser.get_max(name)

            # check min value
            if newMin - one_percent > global_params[name].get_lower_bound():
                global_params[name].set_lower_bound(newMin - one_percent)

            # check max value
            if newMax + one_percent < global_params[name].get_upper_bound():
                global_params[name].set_upper_bound(newMax + one_percent)

            # print min and max to screen after prescan
            global_params.print_bounds(name)

        # get scan density
        density = n_prescan / global_params.volume()

        # get new points
        opt_point = parser.get_max_xb_point(decay)

        # write scan details to details file
        details = open(detailsname, "a")
        details.write("Prescan\n")
        details.write("--------------------\n")
        details.write("Number of prescan points = " + str(n_prescan) + "\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write("Max xsec*BR = " + opt_point.format_xb() + "\n")
        details.write("--------------------\n")
        for name in global_params.parameter_names():
            details.write(name + ":\n")
            details.write("  " + opt_point.format_param(name) + "\n")
            details.write("  " + global_params.parameter(name).format_range() + "\n")
        details.write("--------------------\n")
        details.write("\n\n")
        details.close()

        # write scan results to summary file
        summary = open(summaryname, "a")
        summary.write("Pre")
        summary.write(" " + opt_point.format_xb())
        for name, param in self.__global_params.parameters().items():
            summary.write(" " + f"{opt_point.get_val(name):1.{param.get_precision()}f}")
        summary.write("\n")
        summary.close()

        # scale new low and high values
        # NOTE: Presets scan range before meanshift..
        global_params.scale_ranges(opt_point)

    def __get_random_pos(self):
        params = self.__global_params

        return tuple(
            [
                random.uniform(params[name].get_low(), params[name].get_high())
                for name in params.parameter_names()
            ]
        )

    def __get_initial_positions(self, points_num: int, strategy: str):
        params = self.__global_params

        points = []
        
        if strategy == 'random':
            for i in range(points_num):
                points.append(self.__get_random_pos())
        elif strategy == 'pair':
            initial_point = self.__get_random_pos()
            lead_coeffs = [-1 if p >= 0 else 1 for p in initial_point]
            coeff: float = self.__config_loader.get('meanshift', 'pair_points_coeff') or 0.005
            offsets = [p.width() * coeff for p in params]

            points.append(initial_point)

            next_point = list(deepcopy(initial_point))

            for i in range(1, points_num):
                for i in range(len(next_point)):
                    next_point[i] += lead_coeffs[i] * offsets[i]

                points.append(tuple(deepcopy(next_point)))

        return tuple(points)

    def initialize_directories(self):

        args = self.__args

        scan_path = self.__scan_path
        plot_path = self.__plot_path
        global_params = self.__global_params
        masses = global_params.masses()

        model_name = args.model
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
        for param in global_params:
            summary.write(" " + param.get_fullname())
        summary.write("\n")
        summary.close()

        # Create details file
        detailsname = f"{scan_path}scandetails_{model_name}_{decay}_{masses}.txt"
        details = open(detailsname, "w")
        details.write("Scan details\n\n")
        details.close()