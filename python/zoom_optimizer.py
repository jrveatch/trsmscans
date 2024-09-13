#!/usr/bin/env python3

# import various modules to help with logistics
import shutil
import time
import datetime
import numpy as np
import math
import shutil

# import decimal
from decimal import Decimal

# import tools
from parse import Parse
from utils.point import Point
from utils.params import Params
from filters.filter import apply_filters
from utils.runScannerS import runScannerS
from utils import tsvutils
from utils import fileutils
from utils.config_loader import ConfigLoader

class ZoomOptimizer:

    def __init__(self,
                 params: 'Params',
                 decay: str,
                 num_points: int,
                 starting_max: 'Point',
                 config_loader: ConfigLoader,
                 label: str = ""):

        # some basic scanner information
        self.params = params
        self.decay = decay
        self.num_points = num_points
        self.local_max = starting_max
        self.label = label
        self.model_name = params.model_name()
        self.top_percentile = {}
        self.top_percentile_xb = None
        self.global_xb_fail = 0
        self.is_running = True

        # get zoom configuration from config file
        self.config_loader = config_loader
        try:
            self.strategy: str = self.config_loader.get('zoom', 'strategy')
            self.zoom_percentile: int = self.config_loader.get('zoom', 'zoom_percentile')
            self.parameter_zoom_rate: float = self.config_loader.get('zoom', 'parameter_zoom_rate')
            self.density_growth_rate: float = self.config_loader.get('zoom', 'density_growth_rate')
            self.min_points: int = self.config_loader.get('zoom', 'min_points_per_iteration')
        except KeyError as e:
            print(f"Error: {e}")
            raise
        except Exception as e:
            print(f"Unexpected error: {e}")
            raise

        # set output directory
        self.outdir = fileutils.scan_dir(model_name=self.model_name,
                                         decay=decay,
                                         masses=self.params.masses())

        # get output information file names
        output_file_postfix = self.model_name + "_" + self.decay + "_" + str(self.params.masses()) + ".txt"
        self.summary_name = self.outdir + "scan_summary_" + output_file_postfix
        self.tsv_summary_name = self.outdir + "scan_tsv_summary_" + output_file_postfix
        self.prescan_details_name = self.outdir + "files/details/prescan_details_" + output_file_postfix
        self.details_name = self.outdir + "files/details/scan_details_" + self.label + "_" + output_file_postfix

        # copy prescan details file to zoom optimizer details file
        shutil.copy(self.prescan_details_name,self.details_name)

        # create parse object without a file name
        self.scanparser = Parse(masses=self.params.masses(),
                                model_name=self.model_name)

        # TODO: Names of details and summary files

    def run(self,
            iter: int,
            global_max: 'Point',
            use_multiprocessing: bool = False) -> None:

        # get time of iteration start
        iter_start = time.time()

        # get iteration identifier
        iter_label = f"{iter:04d}"
        if self.label:
            identifier = self.label + "-Iteration-" + iter_label
        print("\nIteration:",identifier)

        # set names of input .ini and output .tsv files
        ini_name = self.outdir + "files/ini/" + self.model_name + "_" + identifier + ".ini"
        tsv_name = self.outdir + "files/tsv/" + self.model_name + "_" + identifier + ".tsv"
        tsv_combined_name = self.outdir + "files/tsv/" + self.model_name + "_" + iter_label + ".tsv"
        tsv_temp_name = self.outdir + self.model_name + ".tsv"

        # write new .ini file from template and parameters
        self.params.write_ini(ini_name)

        # make sure num_points doesn't drop below the minimum
        if self.num_points < self.min_points:
            self.num_points = self.min_points

        # run ScannerS
        self.num_points = runScannerS(ini_name = ini_name,
                                      model_name = self.model_name,
                                      num_points = self.num_points,
                                      use_multiprocessing = use_multiprocessing)

        # TODO: Figure out what to do if process throws a TimeoutError

        # rename output .tsv file to tsv_name
        shutil.move(tsv_temp_name,tsv_name)

        # calculate point density from ranges
        volume = self.params.volume()
        density = self.num_points / volume

        # apply width and bounds filters
        nwidth, nbounds, nsignals, npass = apply_filters(file_name=tsv_name,
                                                         masses=self.params.masses(),
                                                         config_loader=self.config_loader)

        # TODO: Figure out whether these are needed and what return values to use
        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(self.details_name,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            return

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(self.details_name,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            return

        # read output tsv into parser
        self.scanparser.read_file(file_name=tsv_name)

        # get new point as the maximum from the current scan
        new_max = self.scanparser.get_max_xb_point(self.decay)

        # flag to indicate whether new_max is greater than global_max
        is_new_global_max = new_max > global_max

        # store the previous point
        local_max_old = self.local_max

        # if new point is better than the local max point, replace it
        if new_max > self.local_max:
            self.local_max = new_max

        # get iteration end time
        iter_end = time.time()
        iter_time = iter_end - iter_start

        # print iteration time to screen
        print("Iteration took",str(datetime.timedelta(seconds=int(iter_time))),"(hh:mm:ss)")

        # TODO: Factorize this to a function after sample_points change is merged
        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(self.details_name,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("--------------------\n")
        details.write("Using " + str(self.num_points) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write(str(nwidth) + "/" + str(self.num_points) + " pass width cut\n")
        details.write(str(nbounds) + "/" + str(self.num_points) + " pass bounds check\n")
        details.write(str(nsignals) + "/" + str(self.num_points) + " pass signals check\n")
        details.write(str(npass) + "/" + str(self.num_points) + " pass all checks\n")
        details.write("--------------------\n")
        details.write("New max xsec*BR = " + new_max.format_xb() + "\n")
        details.write("Local max xsec*BR = " + self.local_max.format_xb() + "\n")
        details.write("Global max xsec*BR = " + global_max.format_xb() + "\n")
        details.write("Found new global max point: " + str(is_new_global_max) + "\n")
        details.write("--------------------\n")
        for par in self.params.parameter_names():
            details.write(par+":\n")
            details.write("  "+self.params.parameter(par).format_range()+"\n")
            if is_new_global_max:
                details.write("  new global max "+self.local_max.format_param(par)+"\n")
                details.write("  "+self.local_max.format_diff(local_max_old,par)+"\n")
                details.write("  "+self.local_max.format_diff_frac(local_max_old,par)+"\n")
        details.write("--------------------\n")
        details.write("Iteration took "+str(datetime.timedelta(seconds=int(iter_time)))+" (hh:mm:ss)\n")
        details.write("\n\n")
        details.close()

        # if a new optimal point is found
        if is_new_global_max:

            # write max xb point summary to info file
            self.write_summary(identifier)

            # write max xb point raw .tsv line to info file
            self.write_tsv_summary()

        # check zoom strategy and call method accordingly
        match self.strategy:

            # zoom in using percentile
            case "percentile":
                self.percentile_zoom()

            # zoom in using rate
            case "rate":
                self.rate_zoom()

            # all other cases
            case _:
                print("Unrecognized zoom strategy")
                print("Please use 'percentile' (default) or 'rate'")
                # TODO: Throw an exception here
                return

        # append .tsv file to combined .tsv file for iteration
        tsvutils.save_tsv_output(tsv_name, tsv_combined_name)

        # add to a counter if new point is less than half of the global max
        if new_max < global_max * 0.5:
            self.global_xb_fail += 1
        else:
            self.global_xb_fail = 0
        
        # end the ZoomOptimizer if counter reaches 2
        if self.global_xb_fail >= 2:
            self.is_running = False
            end_message = "Local max is consistently less than half of global max\n"
            end_message += "Terminating zoom optimizer"
            print(end_message)
            details = open(self.details_name,"a")
            details.write(end_message)
            details.close()

        return new_max

    # write max xb point summary to info file
    def write_summary(self, identifier) -> None:
        summary = open(self.summary_name,"a")
        summary.write(self.local_max.format_xb())
        for name, par in self.params.parameters().items():
            summary.write("\t" + f"{self.local_max.get_val(name):1.{par.precision()}f}")
        summary.write("\t" + identifier)
        summary.write("\n")
        summary.close()

    # write max xb point raw .tsv line to info file
    def write_tsv_summary(self) -> None:
        tsv_summary = open(self.tsv_summary_name,"a")
        tsv_summary.write(self.scanparser.get_max_xb_line())
        tsv_summary.close()

    # method to zoom in based on a percentile cut on xb
    def percentile_zoom(self) -> None:

        # minimum number of points required before zooming in
        min_points = 10

        # percentile threshold that can be adjusted on the fly
        percentile_threshold = self.zoom_percentile

        # get an array of xb results
        xb_array = self.scanparser.get_xb(self.decay)

        # if top_percentile_xb has already been filled, add it to current xb_array
        if self.top_percentile_xb is not None:
            xb_array = np.append(xb_array, self.top_percentile_xb)

        # ensure min_points are looked
        if len(xb_array) * (1.0 - percentile_threshold / 100) < min_points:
            percentile_threshold = math.floor(100 * (1.0 - min_points/len(xb_array)))

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # create a threshold to look at the top percentile of xb points
        xb_threshold = np.percentile(xb_array, percentile_threshold)

        # get top percentile of xb
        self.top_percentile_xb = xb_array[xb_array > xb_threshold]

        # dictionaries to update low and high in parameters
        low_dict = {}
        high_dict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in self.scanparser.get_parameter_arrays().items():
            # if param is already in top_percentile, add top_percentile to values
            if param in self.top_percentile:
                values = np.append(values, self.top_percentile[param])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > xb_threshold]
            # set lows and highs of each parameter
            low_dict[param] = self.top_percentile[param].min()
            high_dict[param] = self.top_percentile[param].max()

        # update params lows and highs using dictionaries
        self.params.update_low_high(low_dict, high_dict)

        # calculate the new number of points based on the remaining xb range
        height_ratio = (xb_array.max() - xb_threshold) / (xb_array.max() - xb_array.min())
        self.num_points = int(self.num_points * height_ratio * (1.0 + self.density_growth_rate))

        return

    # method to zoom in based on a fixed rate
    def rate_zoom(self) -> None:

        # parameter scaling factor
        range_scale = 1.0 - self.parameter_zoom_rate

        # get volume before zooming
        volume_old = self.params.volume()

        # set new low and high values
        self.params.scale_ranges(self.local_max,range_scale)

        # get volume after zooming
        volume_new = self.params.volume()
        volume_ratio = volume_new / volume_old

        # step down num_points
        self.num_points = int(self.num_points * volume_ratio * (1.0 + self.density_growth_rate))
    
        return
