#!/usr/bin/env python3

# import various modules to help with logistics
import shutil
import time
import datetime
import numpy as np
import math

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

from sample_points import sample_points

class ZoomOptimizer:

    def __init__(self,
                 detailsname: str,
                 summaryname: str,
                 params: 'Params',
                 decay: str,
                 npoints: int,
                 optPoint: 'Point',
                 config_loader: ConfigLoader,
                 label: str = ""):

        # some basic scanner information
        self.detailsname = detailsname
        self.summaryname = summaryname
        self.params = params
        self.decay = decay
        self.npoints = npoints
        self.optPoint = optPoint
        self.label = label
        self.model_name = params.model_name()
        self.top_percentile = {}
        self.top_percentile_xb = None

        self.point_sampler = sample_points(self.outdir, self.params.model_name(), self.maxwidth)

        # get zoom configuration from config file
        self.config_loader = config_loader
        try:
            self.strategy: str = self.config_loader.get('zoom', 'strategy')
            self.zoom_percentile: int = self.config_loader.get('zoom', 'zoom_percentile')
            self.parameter_zoom_rate: float = self.config_loader.get('zoom', 'parameter_zoom_rate')
            self.density_growth_rate: float = self.config_loader.get('zoom', 'density_growth_rate')
            self.minpoints: int = self.config_loader.get('zoom', 'min_points_per_iteration')
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
        
        # TODO: Names of details and summary files

    def run(self,
            iter: int,
            use_multiprocessing: bool = False) -> None:

        # get time of iteration start
        iterstart = time.time()

        # get iteration identifier
        iter_label = f"{iter:04d}"
        if self.label:
            identifier = self.label + "-Iteration-" + iter_label
        print("\nIteration:",identifier)

        self.scanparser = self.point_sampler.pass_info(self.params, identifier, self.decay, self.npoints)


        # calculate point density from ranges
        volume = self.params.volume()
        density = self.npoints / volume
        
        # get new point as the maximum from the current scan
        newPoint = self.scanparser.get_max_xb_point(self.decay)

        # flag to indicate whether optimal point needs to be updated
        update = False

        # store the previous point
        optPointOld = self.optPoint

        # if new point is better than the optimal point, replace it
        if newPoint > self.optPoint:
            update = True
            self.optPoint = newPoint

        # get iteration end time
        iterend = time.time()
        itertime = iterend - iterstart

        # print iteration time to screen
        print("Iteration took",str(datetime.timedelta(seconds=int(itertime))),"(hh:mm:ss)")

        # TODO: Add details about R11, R21, R31
        # write scan details to details file
        details = open(self.detailsname,"a")
        details.write("Iteration = " + str(identifier) + "\n")
        details.write("--------------------\n")
        details.write("Using " + str(self.npoints) + " scan points\n")
        details.write("Scan density = " + f"{Decimal(density):.3E}" + "\n")
        details.write(str(self.point_sampler.get_nwidth()) + "/" + str(self.npoints) + " pass width cut of " + str(self.maxwidth) + "\n")
        details.write(str(self.point_sampler.get_nbounds()) + "/" + str(self.npoints) + " pass bounds check\n")
        details.write(str(self.point_sampler.get_nbounds()) + "/" + str(self.npoints) + " pass signals check\n")
        details.write(str(self.point_sampler.get_npass()) + "/" + str(self.npoints) + " pass both checks\n")
        details.write("--------------------\n")
        details.write("Found new max xsec*BR = " + newPoint.format_xb() + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + self.optPoint.format_xb() + "\n")
        details.write("--------------------\n")
        for par in self.params.parameter_names():
            details.write(par+":\n")
            details.write("  "+self.params.parameter(par).format_range()+"\n")
            if update:
                details.write("  new optimal "+self.optPoint.format_param(par)+"\n")
                details.write("  "+self.optPoint.format_diff(optPointOld,par)+"\n")
                details.write("  "+self.optPoint.format_diff_frac(optPointOld,par)+"\n")
        details.write("--------------------\n")
        details.write("Iteration took "+str(datetime.timedelta(seconds=int(itertime)))+" (hh:mm:ss)\n")
        details.write("\n\n")
        details.close()

        # if a new optimal point is found
        if update is True:
            # write scan results to summary file
            summary = open(self.summaryname,"a")
            summary.write(identifier)
            summary.write(" " + self.optPoint.format_xb())
            for name, par in self.params.parameters().items():
                summary.write(" " + f"{self.optPoint.get_val(name):1.{par.precision()}f}")
            summary.write("\n")
            summary.close()

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
                # TODO: Throw and exception here
                return

        # append .tsv file to combined .tsv file for iteration
        tsvutils.save_tsv_output(tsv_name, tsv_combined_name)

        return

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
        lowdict = {}
        highdict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in self.scanparser.get_parameter_arrays().items():
            # if param is already in top_percentile, add top_percentile to values
            if param in self.top_percentile:
                values = np.append(values, self.top_percentile[param])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > xb_threshold]
            # set lows and highs of each parameter
            lowdict[param] = self.top_percentile[param].min()
            highdict[param] = self.top_percentile[param].max()

        # update params lows and highs using dictionaries
        self.params.update_low_high(lowdict, highdict)

        # calculate the new number of points based on the remaining xb range
        heightRatio = (xb_array.max() - xb_threshold) / (xb_array.max() - xb_array.min())
        self.npoints = int(self.npoints * heightRatio * (1.0 + self.density_growth_rate))

        return

    # method to zoom in based on a fixed rate
    def rate_zoom(self) -> None:

        # parameter scaling factor
        range_scale = 1.0 - self.parameter_zoom_rate

        # get volume before zooming
        volume_old = self.params.volume()

        # set new low and high values
        self.params.scale_ranges(self.optPoint,range_scale)

        # get volume after zooming
        volume_new = self.params.volume()
        volume_ratio = volume_new / volume_old

        # step down npoints
        self.npoints = int(self.npoints * volume_ratio * (1.0 + self.density_growth_rate))
    
        return