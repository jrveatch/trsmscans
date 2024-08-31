#!/usr/bin/env python3

# import various modules to help with logistics
import os
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

class ZoomOptimizer:

    def __init__(self,
                 detailsname: str,
                 summaryname: str,
                 params: 'Params',
                 decay: str,
                 maxwidth: float,
                 npoints: int,
                 optPoint: 'Point',
                 percentile: float,
                 outdir: str,
                 parameter_rate: float,
                 density_growth_rate: float,
                 label: str = ""):

        # some basic scanner information
        self.detailsname = detailsname
        self.summaryname = summaryname
        self.params = params
        self.decay = decay
        self.maxwidth = maxwidth
        self.npoints = npoints
        self.optPoint = optPoint
        self.outdir = outdir
        self.label = label
        self.modelname = params.model_name()
        self.percentile = percentile
        self.top_percentile = {}
        self.top_percentile_xb = None
        
        self.parRate = parameter_rate
        self.densityRate = density_growth_rate

        # set minimum number of points per iteration
        self.minpoints = 100

        # create parse object without a filename
        self.scanparser = Parse(masses=self.params.masses(),
                                modelname=self.modelname,
                                decay=self.decay)

        # TODO: Names of details and summary files

    def run(self,
            iter: int,
            use_multiprocessing: bool = False) -> None:

        # get time of iteration start
        iterstart = time.time()

        # get iteration identifier
        identifier = f"{iter:04d}"
        if self.label:
            identifier = self.label + "_" + identifier
        print("\nIteration:",identifier)

        # set names of input .ini and output .tsv files
        ininame = self.outdir + "files/ini/" + self.modelname + "_" + identifier + ".ini"
        tsvname = self.outdir + "files/tsv/" + self.modelname + "_" + identifier + ".tsv"
        temptsv = self.outdir + self.modelname + ".tsv"

        # write new .ini file from template and parameters
        self.params.write_ini(ininame)

        # make sure npoints doesn't drop below the minimum
        if self.npoints < self.minpoints:
            self.npoints = self.minpoints

        # run ScannerS
        self.npoints = runScannerS(ininame=ininame,
                                   modelname=self.modelname,
                                   npoints=self.npoints,
                                   use_multiprocessing=use_multiprocessing)

        # TODO: Figure out what to do if process returns negative value

        # rename output .tsv file to tsvname
        shutil.move(temptsv,tsvname)

        # calculate point density from ranges
        volume = self.params.volume()
        density = self.npoints / volume

        # apply width and bounds filters
        nwidth, nbounds, npass = apply_filters(filename=tsvname,
                                                       masses=self.params.masses(),
                                                       modelname=self.modelname,
                                                       maxwidth=self.maxwidth)

        # TODO: Figure out whether these are needed and what return values to use
        # protection against the case where all points fail width filter
        if nwidth == 0:
            details = open(self.detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nwidth) + " events passing width filter\n")
            details.write("\n\n\n\n")
            details.close()
            return

        # protection against the case where all points fail bounds filter
        if nbounds == 0:
            details = open(self.detailsname,"a")
            details.write("Iteration = " + str(identifier) + "\n")
            details.write("Skip due to " + str(nbounds) + " events passing bounds filter\n")
            details.write("\n\n")
            details.close()
            return

        # read output tsv into parser
        self.scanparser.read_file(filename=tsvname)

        # get new point as the maximum from the current scan
        newPoint = self.scanparser.get_max_xb_point()

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
        details.write(str(nwidth) + "/" + str(self.npoints) + " pass width cut of " + str(self.maxwidth) + "\n")
        details.write(str(nbounds) + "/" + str(self.npoints) + " pass bounds check\n")
        details.write(str(npass) + "/" + str(self.npoints) + " pass both checks\n")
        details.write("--------------------\n")
        details.write("Found new max xsec*BR = " + newPoint.format_xb() + "\n")
        details.write("Update optimal point: " + str(update) + "\n")
        details.write("Optimal point xsec*BR = " + self.optPoint.format_xb() + "\n")
        details.write("--------------------\n")
        for par in self.params.parnames():
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

        # get paramaters to use for zooming in
        paramArrays = self.scanparser.get_parameter_arrays()

        # minimum amount of points that need to be looked at before zooming in
        min_points = 10
        percentile_threshold = self.percentile

        # get an array of xb results
        xb_array = self.scanparser.get_xb()

        # if not the first iteration, add top_percentile_xb to current xb_array
        if iter != 0:
            xb_array = np.append(xb_array, self.top_percentile_xb)

        # ensure min_points are looked
        if len(xb_array) * (1.0 - percentile_threshold / 100) < min_points:
            percentile_threshold = math.floor(100 * (1.0 - min_points/len(xb_array)))

        # make sure percentile threshold is >= 0
        if percentile_threshold < 0:
            percentile_threshold = 0

        # create a threshold to look at the top percentile of xb points
        threshold = np.percentile(xb_array, percentile_threshold)

        # get top percentile of xb
        self.top_percentile_xb = xb_array[xb_array > threshold]

        # dictionaries to update low and high in parameters
        lowdict = {}
        highdict = {}

        # save params arrays where xb_array is the top percentile
        for param, values in paramArrays.items():
            # if not first iteration, add top_percentile to values
            if iter != 0:
                values = np.append(values, self.top_percentile[param])
            # update top_percentile accounting for new values
            self.top_percentile[param] = values[xb_array > threshold]
            # set lows and highs of each parameter
            lowdict[param] = self.top_percentile[param].min()
            highdict[param] = self.top_percentile[param].max()

        # update low and high using dictionaries
        self.params.update_low_high(lowdict, highdict)

        # TODO: reinclude old scaling as an alternative
        # parameter scaling factor
        #rangeScale = 1.0 - self.zoom.parRate

        # set new low and high values
        #self.params.scale_ranges(self.optPoint,rangeScale)

        # TODO: include these two lines in old scaling alternative
        # get new volume
        #volumeNew = self.params.volume()
        #volumeRatio = volumeNew/volume

        # step down npoints
        # self.npoints = int(self.npoints * volumeRatio * (1.0 + self.zoom.densityRate))
        
        heightRatio = (xb_array.max() - threshold) / (xb_array.max() - xb_array.min())
        self.npoints = int(self.npoints * heightRatio * (1.0 + self.densityRate))

        return