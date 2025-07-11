#!/usr/bin/env python3

import argparse
import multiprocessing as mp
from tqdm import tqdm

from utils.cpu_utils import get_n_cpus
from mass_grid.mass_json_utils import get_mass_permutations
from utils.model import Model, supported_models
from plot.plot_meanshift import MeanShiftPlotter
from plot.plot_zoom import ZoomPlotter

def plot_mass_point(args):
    xmass, smass, hmass, decay, model_name, strategy = args
    model = Model(name=model_name, masses={"H": hmass, "S": smass, "X": xmass})
    if not model.is_calculable:
        print(f"{model.mass_string} is not calculable. Skipping...")
        return

    try:
        if strategy == "zoom":
            plotter = ZoomPlotter(decay=decay, model=model)
            plotter.make_scan_plots()
            plotter.make_max_xb_plots()
        elif strategy == "meanshift":
            plotter = MeanShiftPlotter(model=model, decay=decay)
            plotter.make_mean_shift_plots()
    except Exception as e:
        print(f"Error while plotting {model.mass_string}: {e}")

def main():

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    arg_parser.add_argument("-l", "--use-mass-list", action="store_true", help="Run over a mass list instead of a single mass point")
    arg_parser.add_argument("-X", "--XMass", type=float, help="Mass of heavy scalar X in GeV")
    arg_parser.add_argument("-S", "--SMass", type=float, help="Mass of scalar S in GeV")
    arg_parser.add_argument("-H", "--HMass", default=125.09, type=float, help="Mass of scalar H in GeV")
    arg_parser.add_argument("-i", "--identifier", type=str, help="Mass set identifier")
    arg_parser.add_argument("-m", "--model", default="TRSMBroken", type=str, choices=supported_models, help="Model name")
    arg_parser.add_argument("-d", "--decay", type=str, help="Decay mode")
    arg_parser.add_argument("-s", "--strategy", default="zoom", type=str, choices=['zoom','meanshift'], help="Optimization strategy")
    args = arg_parser.parse_args()

    # Load mass points
    if args.use_mass_list:
        if not args.decay:
            raise ValueError("Decay mode (-d/--decay) is required to run over a mass list")
        if not args.identifier:
            raise ValueError("Identifier (-i/--identifier) is required to run over a mass list")
        permutations = get_mass_permutations(decay=args.decay, identifier=args.identifier)
        mass_points = [(x, s, args.HMass) for x, s, _, _ in permutations]
        print(f"Loaded {len(mass_points)} mass points from identifier '{args.identifier}' with decay '{args.decay}'")
    elif args.XMass and args.SMass:
        mass_points = [(args.XMass, args.SMass, args.HMass)]
    else:
        raise ValueError("Please specify either -l/--use-mass-list or provide -X/--XMass and -S/--SMass")

    args_list = [(x, s, h, args.decay, args.model, args.strategy) for (x, s, h) in mass_points]
    with mp.Pool(processes=get_n_cpus()) as pool:
        for _ in tqdm(pool.imap_unordered(plot_mass_point, args_list), total=len(args_list)):
            pass

if __name__ == "__main__":
    mp.set_start_method("spawn")
    main()
