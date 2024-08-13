#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil

# import decimal
from decimal import Decimal

# import tools
from parse import Parse
from utils.point import Point
from utils.params import Params
import filters
from utils.runScannerS import runScannerS
from scan import Scan


from typing import List

class to_be_named:
        
    def __init__(self, params: Params, outdir, identifier) -> Parse:

        self.outdir = outdir
        self.params = params
        self.modelName = params.model_name()

        # set names of input .ini and output .tsv files
        outname = self.outdir + "files/" + self.modelname + "_" + identifier
        ininame = outname + ".ini"
        tsvname = outname + ".tsv"
        temptsv = self.outdir + self.modelname + ".tsv"
            
        # write new .ini file from template and parameters
        self.params.write_ini(ininame)

       # parser = Parse(masses=params.masses(), decay: str, self.modelName, temptsv)

        # run ScannerS
        self.npoints = runScannerS(ininame=ininame,
                                modelname=self.modelname,
                                npoints=self.npoints,
                                use_multiprocessing=use_multiprocessing)

        # TODO: Figure out what to do if process returns negative value

        # rename output .tsv file to tsvname
        shutil.move(temptsv,tsvname)
        
        def deal_with_points(self):

            # calculate point density from ranges
            volume = self.params.volume()
            density = self.npoints / volume

            # apply width and bounds filters
            nwidth, nbounds, npass = filters.apply_filters(filename=tsvname,
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