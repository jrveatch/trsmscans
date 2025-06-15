#!/usr/bin/env python3

# TODO: Make sure to pip yes to overwrite existing scans

import argparse
import os

from utils.file_utils import prescan_dir, scan_dir
from utils.logging_utils import LOG_LEVELS, setup_logging
from prescan.prescan import prescan
from scan.scan import Scan
from utils.model import Model
from utils.parse import Parse
from mass_grid.mass_json_utils import get_mass_permutations

def run_prescan(model: Model,
                num_points: int,
                overwrite: bool,
                log_level: int) -> Parse:

    setup_logging(log_file=os.path.join(prescan_dir(model),"prescan.log"),
                  level=log_level)

    return prescan(model=model,
                   num_points=num_points,
                   overwrite=overwrite)

def run_scan(model: Model,
             decay: str,
             strategy: str,
             num_points: int,
             prescan_points: int,
             overwrite: bool,
             iterations: int,
             log_level: int) -> None:

    setup_logging(log_file=os.path.join(scan_dir(model=model,
                                                 decay=decay),f"{strategy}.log"),
                  level=log_level)

    scan = Scan(model=model, decay=decay, prescan_points=prescan_points, overwrite=overwrite)
    if strategy == "zoom":
        scan.run_zoom_optimization(num_points=num_points, niter=iterations)
    elif strategy == "meanshift":
        scan.run_ms_optimization(num_optimizers=iterations)
    else:
        raise ValueError(f"Invalid strategy: {strategy}")

def main():

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("--mode", type=str, choices=["scan", "prescan"], required=True, help="Mode of operation: 'scan' or 'prescan'")
    arg_parser.add_argument("-b", "--batch", action="store_true", help="Submit to HTCondor instead of running interactively")
    arg_parser.add_argument("-l", "--use-mass-list", action="store_true", help="Run over a mass list instead of a single mass point")
    arg_parser.add_argument("-X", "--XMass", type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-i", "--identifier", type=str, help="Mass set identifier")
    arg_parser.add_argument("-m", "--model", required=True, type=str, help="Model name")
    arg_parser.add_argument("-d", "--decay", type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", type=str, choices=['zoom','meanshift'], help="Scan strategy")
    arg_parser.add_argument("-n", "--num-points", required=True, type=int, help="Initial number of scan points")
    arg_parser.add_argument("-p", "--prescan_points", default=-1, type=int, help="Number of prescan points when using scan mode")
    arg_parser.add_argument("-t", "--iterations", default=-1, type=int, help="Maximum number of iterations/optimizers")
    arg_parser.add_argument("-o", "--overwrite", action="store_true", help="Overwrite previous scan")
    arg_parser.add_argument("--log-level", default="info", choices=LOG_LEVELS.keys(), help="Set the logging level")
    args = arg_parser.parse_args()

    log_level = LOG_LEVELS[args.log_level.lower()]

    # Load mass points
    if args.use_mass_list:
        if not args.decay:
            raise ValueError("Decay mode is required to run over a mass list")
        if not args.identifier:
            raise ValueError("Identifier is required to run over a mass list")
        permutations = get_mass_permutations(decay=args.decay, identifier=args.identifier)
        mass_points = [(x, s, args.HMass) for x, s, _ in permutations]
    elif args.XMass and args.SMass:
        mass_points = [(args.XMass, args.SMass, args.HMass)]
    else:
        raise ValueError("Must specify either --use-mass-list or provide --XMass and --SMass")

    for xmass, smass, hmass in mass_points:
        model = Model(name=args.model, masses={"H": hmass, "S": smass, "X": xmass})
        if args.batch:
            pass
            #submit_htcondor(args.mode, xmass, smass, args.model, args.decay, args.strategy, args.num_points)
        else:
            if args.mode == "prescan":
                run_prescan(model=model,
                            num_points=args.num_points,
                            overwrite=args.overwrite,
                            log_level=log_level)
            else:
                if not args.decay or not args.strategy:
                    raise ValueError("Scan mode requires --decay and --strategy")
                run_scan(model=model,
                         decay=args.decay,
                         strategy=args.strategy,
                         num_points=args.num_points,
                         prescan_points=args.prescan_points,
                         overwrite=args.overwrite,
                         iterations=args.iterations,
                         log_level=log_level)

if __name__ == "__main__":
    main()
