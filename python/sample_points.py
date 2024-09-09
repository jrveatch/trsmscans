#!/usr/bin/env python3

# import various modules to help with logistics
import os
import shutil

# import tools
import filters.filter
from parse import Parse
from utils.params import Params
import filters.filter
from utils.runScannerS import runScannerS

from utils import tsvutils


from typing import List

class sample_points:
        
    def __init__(self, outdir: str, model_name: str, maxwidth: float) -> None:

        self.outdir = outdir
        self.model_name = model_name
        self.maxwidth = maxwidth

    def pass_info(self, params: Params, identifier: str, decay: str, npoints: int) -> Parse:

        # set names of input .ini and output .tsv files
        outname = self.outdir + "files/" + self.model_name + "_" + identifier
        self.ininame = outname + ".ini"
        tsvname = outname + ".tsv" 
        temptsv = self.outdir + self.model_name + ".tsv"

        self.npoints = npoints
            
        # write new .ini file from template and parameters
        params.write_ini(self.ininame)

        self.parser = Parse(params.masses(), decay, self.model_name)

        valid_points = 0

        self.nwidth = 0
        self.nbounds = 0
        self.npass = 0

        curr_points_run: int = 0
        #curr_points_run = int(curr_points_run)

        while self.npass < self.npoints:

            points = runScannerS(ininame=self.ininame,
                         modelname=self.model_name,
                         npoints=npoints,
                         use_multiprocessing=True)

            curr_points_run += npoints
            valid_points += points

            # apply width and bounds filters
            nwidth, nbounds, npass = filters.filter.apply_filters(filename=temptsv,
                                                    masses=params.masses(),
                                                    modelname=self.model_name,
                                                    maxwidth=self.maxwidth)
            
            tsvutils.save_tsv_output(temptsv, tsvname)
            
            self.npass += npass
            self.nbounds += nbounds
            self.nwidth += nwidth

            efficiency = self.npass/curr_points_run

            efficiency *= 1.05

            """
            10000(1-E)/E --- 3000/E
            """

            npoints = (self.npoints-self.npass)/efficiency



        '''self._generate_points(npoints)

        # rename output .tsv file to tsvname
        shutil.move(temptsv,tsvname)'''
        
        
        '''# apply width and bounds filters
        self.nwidth, self.nbounds, self.npass = filters.filter.apply_filters(filename=tsvname,
                                                    masses=params.masses(),
                                                    modelname=self.model_name,
                                                    maxwidth=self.maxwidth)
        '''
        # read output tsv into parser
        self.parser.read_file(filename=tsvname)
        # TODO: Figure out what to do if process returns negative value

        return self.parser

    #Set the variables
    def set_nwidth(self, nwidth: float):
        self.nwidth = nwidth

    def set_nbounds(self, nbounds):
        self.nbounds = nbounds

    def set_npass(self, npass):
        return self.npass
    
    #Return the variables
    def get_nwidth(self) -> float:
        return self.nwidth
    
    def get_nbounds(self):
        return self.nbounds
    
    def get_npass(self):
        return self.npass
    

if __name__ == "__main__":
    pass
