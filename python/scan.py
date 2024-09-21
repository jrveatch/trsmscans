#!/usr/bin/env python3

# import various modules to help with logistics
import argparse

# import tools
from utils.masses import Masses

from zoom_scanner import ZoomScanner
from mean_shift_scanner import MeanShiftScanner

if __name__ == "__main__":

    # Parse command line arguments
    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-X", "--XMass", required=True, type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", required=True, type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-M", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", required=True, type=str, help="Decay mode")
    arg_parser.add_argument("-n", "--npoints", default=-1, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-i", "--iterations", default=20, type=int, help="Maximum number of iterations")
    arg_parser.add_argument("-op", "--optimizer", default="zoom", type=str, help="Optimization strategy, try 'zoom' or 'ms'")
    arg_parser.add_argument("-m", "--multiprocessing", action="store_true", help="Whether multiprocessing should be used")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Whether overwrite should be used")
    args = arg_parser.parse_args()

    # create masses object
    masses = Masses(mX=args.XMass, mS=args.SMass, mH=args.HMass)

    if args.optimizer == "zoom":
        # create scan object
        myScan = ZoomScanner(masses = masses,
                    model_name = args.model,
                    decay = args.decay,
                    overwrite = args.overwrite
                    )

        # run scan using scan object
        myScan.run_zoom_optimization(num_points = args.npoints,
                                    niter = args.iterations,
                                    use_multiprocessing = args.multiprocessing)
    elif args.optimizer == "ms":
        scanner = MeanShiftScanner(args)

        scanner.run()
    else:
        print("Warning: Optimizer not defined, exiting")
